import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from config import PHASE_EXPLORE, PHASE_WELCOME
from data import load_annotations


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
        if st.button("Back to exploration"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        return

    scored = [a for a in annotations if a.get("scores")]
    if scored:
        st.subheader("Average Scores by Model")
        model_data = {}
        for ann in scored:
            model = ann["model_name"]
            if model not in model_data:
                model_data[model] = {"Authenticity": [], "Diversity": [], "Respectfulness": []}
            model_data[model]["Authenticity"].append(ann["scores"]["authenticity"])
            model_data[model]["Diversity"].append(ann["scores"]["diversity"])
            model_data[model]["Respectfulness"].append(ann["scores"]["respectfulness"])

        chart = {m: {k: sum(v) / len(v) for k, v in scores.items()} for m, scores in model_data.items()}
        st.bar_chart(pd.DataFrame(chart).T)

    refusals = [a for a in annotations if a.get("status") == "refused"]
    if refusals:
        st.markdown("---")
        st.subheader(f"Model Refusals ({len(refusals)})")
        for ref in refusals:
            with st.expander(f'{ref["model_name"]} refused: "{ref["prompt"]}"'):
                st.markdown(f"**Significance:** {ref.get('refusal_note', '')}")

    st.markdown("---")
    st.subheader("All Annotations")
    for ann in annotations:
        ptype = "[Shared]" if ann.get("prompt_type") == "shared" else "[Free]"
        refused = ann.get("status") == "refused"
        label = f'{ptype} {ann["model_name"]} — "{ann["prompt"][:50]}"'
        if refused:
            label += " (refused)"

        with st.expander(label):
            if refused:
                st.warning("Model refused to generate")
                st.markdown(f"**Significance:** {ann.get('refusal_note', '')}")
            else:
                scores = ann.get("scores", {})
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Authenticity", f"{scores.get('authenticity', '?')}/5")
                with cols[1]:
                    st.metric("Diversity", f"{scores.get('diversity', '?')}/5")
                with cols[2]:
                    st.metric("Respectfulness", f"{scores.get('respectfulness', '?')}/5")
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
        if st.button("Back to exploration"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
    with col2:
        if st.button("Finish Workshop"):
            st.balloons()
            st.session_state.current_phase = PHASE_WELCOME
            st.session_state.participant_id = None
            st.rerun()
