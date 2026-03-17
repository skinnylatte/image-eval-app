import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from config import BLIND_NAMES, PHASE_EXPLORE, PHASE_WELCOME
from data import load_annotations


def _display_name(ann: dict) -> str:
    return ann.get("blind_name") or BLIND_NAMES.get(ann.get("model"), ann.get("model_name", "Unknown"))


def run():
    st.title("Your Results")
    st.markdown(
        f"**{st.session_state.participant_display_name}** "
        f"({st.session_state.participant_background})"
    )
    st.markdown("---")

    annotations = load_annotations(st.session_state.participant_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Prompts Generated", len(st.session_state.get("prompts", [])))
    with col2:
        st.metric("Image Sets", len(st.session_state.get("generated_images", {})))
    with col3:
        st.metric("Annotations", len(annotations))

    st.markdown("---")

    if not annotations:
        st.info("Complete some annotations to see your results here.")
        if st.button("Write a new prompt"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        return

    scored = [a for a in annotations if a.get("scores")]
    if scored:
        st.subheader("Average Scores by System")
        model_data = {}
        for ann in scored:
            name = _display_name(ann)
            if name not in model_data:
                model_data[name] = {"Authenticity": [], "Diversity": [], "Respectfulness": []}
            for key, field in [("Authenticity", "authenticity"), ("Diversity", "diversity"), ("Respectfulness", "respectfulness")]:
                val = ann["scores"].get(field)
                if val is not None:
                    model_data[name][key].append(val)

        chart = {m: {k: sum(v) / len(v) for k, v in scores.items() if v} for m, scores in model_data.items()}
        st.bar_chart(pd.DataFrame(chart).T)

    refusals = [a for a in annotations if a.get("status") == "refused"]
    if refusals:
        st.markdown("---")
        st.subheader(f"Refusals ({len(refusals)})")
        for ref in refusals:
            name = _display_name(ref)
            with st.expander(f'{name} refused: "{ref["prompt"]}"'):
                st.markdown(f"**Significance:** {ref.get('refusal_note', '')}")

    st.markdown("---")
    st.subheader("All Annotations")
    for ann in annotations:
        name = _display_name(ann)
        ptype = "[Shared]" if ann.get("prompt_type") == "shared" else "[Free]"
        refused = ann.get("status") == "refused"
        label = f'{ptype} {name} -"{ann["prompt"][:50]}"'
        if refused:
            label += " (refused)"

        with st.expander(label):
            if refused:
                st.warning(f"{name} refused to generate")
                st.markdown(f"**Significance:** {ann.get('refusal_note', '')}")
            else:
                scores = ann.get("scores", {})
                cols = st.columns(3)
                for col, label, field in zip(cols, ["Authenticity", "Diversity", "Respectfulness"],
                                             ["authenticity", "diversity", "respectfulness"]):
                    with col:
                        val = scores.get(field)
                        st.metric(label, f"{val}/5" if val is not None else "N/A")
                st.markdown(f"**Expected vs. Actual:** {ann.get('expectation', '')}")
                st.markdown(f"**Authenticity:** {ann.get('authenticity_note', '')}")
                st.markdown(f"**Significance:** {ann.get('harm_note', '')}")

    st.markdown("---")
    export = json.dumps({
        "participant_id": st.session_state.participant_id,
        "background": st.session_state.participant_background,
        "prompts": st.session_state.get("prompts", []),
        "annotations": annotations,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2)
    st.download_button("Download Your Data (JSON)", export,
                       file_name=f"{st.session_state.participant_id}_results.json",
                       mime="application/json")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Write a new prompt"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
    with col2:
        if st.button("Finish Workshop"):
            st.balloons()
            st.session_state.current_phase = PHASE_WELCOME
            st.session_state.participant_id = None
            st.rerun()
