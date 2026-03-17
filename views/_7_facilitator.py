import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from config import MODELS, SHARED_PROMPTS, SCORE_FIELDS, PHASE_WELCOME
from data import load_all_annotations, load_all_identities
from analysis import (
    aggregate_scores,
    analyze_refusals,
    compute_inter_rater_reliability,
    extract_low_scores,
    extract_quotes,
    summary_table,
    generate_report,
)


def run():
    st.title("Facilitator Dashboard")

    with st.sidebar:
        st.markdown("### Controls")
        auto_refresh = st.toggle("Auto-refresh (30s)", value=False)
        if st.button("Refresh now"):
            st.rerun()
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.participant_id = None
            st.session_state.current_phase = PHASE_WELCOME
            st.rerun()

    if auto_refresh:
        st.html('<meta http-equiv="refresh" content="30">')

    identities = load_all_identities()
    annotations = load_all_annotations()

    _render_pulse(identities, annotations)
    _render_participant_progress(identities, annotations)
    _render_patterns(annotations)
    _render_alerts(annotations)
    _render_export(annotations)


def _render_pulse(identities, annotations):
    st.header("Workshop Pulse")
    n_registered = len(identities)
    n_annotating = len(set(a["participant_id"] for a in annotations))
    n_annotations = len(annotations)
    n_prompts = len(set((a["participant_id"], a["prompt"]) for a in annotations))
    n_refusals = sum(1 for a in annotations if a.get("status") == "refused")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Registered", n_registered)
    col2.metric("Annotating", n_annotating)
    col3.metric("Annotations", n_annotations)
    col4.metric("Unique Prompts", n_prompts)
    col5.metric("Refusals", n_refusals)
    st.markdown("---")


def _render_participant_progress(identities, annotations):
    st.header("Participant Progress")

    by_participant = {}
    for a in annotations:
        by_participant.setdefault(a["participant_id"], []).append(a)

    rows = []
    for identity in identities:
        pid = identity.get("anonymous_id", "")
        anns = by_participant.get(pid, [])
        n_shared = sum(1 for a in anns if a.get("prompt_type") == "shared")
        n_free = sum(1 for a in anns if a.get("prompt_type") == "free")
        n_total = len(anns)

        if n_total == 0:
            status = "Registered"
        elif n_shared < len(SHARED_PROMPTS) * len(MODELS):
            status = f"Shared ({n_shared})"
        else:
            status = f"Exploring ({n_free} free)"

        timestamps = [a.get("timestamp", "") for a in anns]
        last_active = max(timestamps) if timestamps else identity.get("registered_at", "")

        rows.append({
            "ID": pid,
            "Name": identity.get("name", ""),
            "Background": identity.get("background", ""),
            "Shared": n_shared,
            "Free": n_free,
            "Total": n_total,
            "Status": status,
            "Last Active": last_active[:19].replace("T", " "),
        })

    if rows:
        df = pd.DataFrame(rows).sort_values("Total", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No participants registered yet.")
    st.markdown("---")


def _render_patterns(annotations):
    st.header("Emerging Patterns")

    if not annotations:
        st.info("Waiting for annotations...")
        return

    tab_summary, tab_models, tab_irr, tab_low, tab_quotes = st.tabs([
        "Summary", "By Model", "Inter-Rater Reliability", "Low Scores", "Quotes",
    ])

    with tab_summary:
        st.dataframe(summary_table(annotations), use_container_width=True, hide_index=True)

    with tab_models:
        model_scores = aggregate_scores(annotations, "model_name")
        if model_scores:
            chart_data = {}
            for model, stats in model_scores.items():
                chart_data[model] = {
                    f.title(): stats.get(f"{f}_mean", 0) or 0 for f in SCORE_FIELDS
                }
            st.bar_chart(pd.DataFrame(chart_data).T)

            ref = analyze_refusals(annotations)
            if ref["total"] > 0:
                st.subheader(f"Refusals: {ref['total']} total")
                for model, entries in ref["by_model"].items():
                    with st.expander(f"{model}: {len(entries)} refusals"):
                        for e in entries:
                            st.markdown(f"- **{e['prompt']}**: {e['note'][:200]}")

    with tab_irr:
        irr = compute_inter_rater_reliability(annotations)
        if irr:
            irr_rows = []
            for key, stats in irr.items():
                row = {"Prompt | Model": key, "Raters": stats["n_raters"]}
                for f in SCORE_FIELDS:
                    m = stats.get(f"{f}_mean")
                    r = stats.get(f"{f}_range")
                    if m is not None:
                        row[f"{f.title()} (M)"] = f"{m:.2f}"
                        row[f"{f.title()} (Range)"] = r
                irr_rows.append(row)
            st.dataframe(pd.DataFrame(irr_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Need shared prompt annotations from multiple participants.")

    with tab_low:
        findings = extract_low_scores(annotations)
        has_findings = any(findings[f] for f in SCORE_FIELDS)
        if has_findings:
            for field in SCORE_FIELDS:
                items = findings[field]
                if not items:
                    continue
                st.subheader(f"Low {field.title()} (score <= 2)")
                for model, issues in items.items():
                    with st.expander(f"{model}: {len(issues)} issues"):
                        for iss in issues:
                            bg = f" [{iss['background']}]" if iss.get("background") else ""
                            st.markdown(f"- \"{iss['prompt']}\"{bg} (score: {iss['score']})")
        else:
            st.info("No low scores yet.")

    with tab_quotes:
        quotes = extract_quotes(annotations)
        if quotes:
            for q in quotes:
                bg = f" [{q['background']}]" if q.get("background") else ""
                with st.expander(f"{q['model']} -- \"{q['prompt'][:40]}\"{bg}"):
                    st.markdown(f"> {q['quote']}")
                    st.caption(f"Field: {q['field']} | Participant: {q['participant']}")
        else:
            st.info("No substantial written responses yet.")

    st.markdown("---")


def _render_alerts(annotations):
    st.header("Alerts")

    if not annotations:
        return

    alerts = []

    ref = analyze_refusals(annotations)
    for model, entries in ref.get("by_model", {}).items():
        if len(entries) >= 3:
            alerts.append(f"**{model}** has {len(entries)} refusals.")

    model_scores = aggregate_scores(annotations, "model_name")
    for model, stats in model_scores.items():
        for f in SCORE_FIELDS:
            mean = stats.get(f"{f}_mean")
            if mean is not None and mean < 2.0 and stats["n"] >= 3:
                alerts.append(f"**{model}** has mean {f} of {mean:.1f} across {stats['n']} annotations.")

    irr = compute_inter_rater_reliability(annotations)
    for key, stats in irr.items():
        for f in SCORE_FIELDS:
            r = stats.get(f"{f}_range")
            if r is not None and r >= 4 and stats["n_raters"] >= 2:
                alerts.append(f"High disagreement on **{key}** for {f}: range of {r}.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No alerts. Workshop running smoothly.")

    st.markdown("---")


def _render_export(annotations):
    st.header("Data Export")

    if not annotations:
        st.info("No data to export yet.")
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "All Annotations (JSON)",
            json.dumps(annotations, indent=2),
            file_name=f"all_annotations_{ts}.json",
            mime="application/json",
        )
    with col2:
        st.download_button(
            "Summary (CSV)",
            summary_table(annotations).to_csv(index=False),
            file_name=f"summary_{ts}.csv",
            mime="text/csv",
        )
    with col3:
        st.download_button(
            "Full Report (Markdown)",
            generate_report(annotations),
            file_name=f"report_{ts}.md",
            mime="text/markdown",
        )

    with st.expander("Preview Report"):
        st.markdown(generate_report(annotations))
