import random

import streamlit as st
from config import BLIND_NAMES, BIAS_CATEGORIES, MODELS, PHASE_ANNOTATE, PHASE_EXPLORE
from components import render_model_card, read_scores, read_refusal_note, validate_scores_only, is_nonsensical


def run():
    results = st.session_state.get("current_prompt_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})
    prompt_text = prompt_meta.get("prompt", "")
    category = prompt_meta.get("category", "")

    if "gallery_order" not in st.session_state:
        order = list(results.keys())
        random.shuffle(order)
        st.session_state.gallery_order = order
    display_order = st.session_state.gallery_order

    ratable = [mk for mk in display_order if results.get(mk, {}).get("status") in ("success", "refused")]
    errored = [mk for mk in display_order if results.get(mk, {}).get("status") not in ("success", "refused")]

    st.title("Compare and Score")
    st.subheader(f'"{prompt_text}"')
    if category:
        st.caption(f"Category: {BIAS_CATEGORIES.get(category, category)}")
    st.markdown("Score each system while comparing them side by side.")
    st.markdown("---")

    per_row = 3
    for i in range(0, len(ratable), per_row):
        row = ratable[i:i + per_row]
        cols = st.columns(per_row)
        for col, mk in zip(cols, row):
            with col:
                prefix = f"gallery_{mk}"
                render_model_card(mk, results[mk], prefix)

    for mk in errored:
        msg = results[mk].get("message", "Unknown error")[:100]
        st.error(f"**{BLIND_NAMES[mk]}** failed: {msg}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to exploration", use_container_width=True):
            st.session_state.pop("gallery_order", None)
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
    with col2:
        if not ratable:
            st.warning("No systems produced results to rate.")
        elif st.button("Continue to written responses", type="primary", use_container_width=True):
            all_valid = True
            scored_models = {}

            for mk in ratable:
                prefix = f"gallery_{mk}"
                if results[mk].get("status") == "refused":
                    note = read_refusal_note(prefix)
                    if not note:
                        st.error(f"Please explain the significance of **{BLIND_NAMES[mk]}**'s refusal.")
                        all_valid = False
                    else:
                        scored_models[mk] = {"status": "refused", "refusal_note": note}
                else:
                    scores = read_scores(prefix)
                    if not validate_scores_only(scores):
                        all_valid = False
                    else:
                        scored_models[mk] = {"status": "success", "scores": scores}

            if all_valid:
                st.session_state.scored_models = scored_models
                text_queue = [mk for mk, data in scored_models.items()
                              if data["status"] == "success" and not is_nonsensical(data["scores"])]
                st.session_state.text_queue = text_queue
                st.session_state.text_queue_idx = 0
                st.session_state.pop("gallery_order", None)
                st.session_state.current_phase = PHASE_ANNOTATE
                st.rerun()
