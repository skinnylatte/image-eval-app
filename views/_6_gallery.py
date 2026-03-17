import random

import streamlit as st
from config import BLIND_NAMES, BIAS_CATEGORIES, PHASE_ANNOTATE, PHASE_EXPLORE
from components import show_gallery


def run():
    results = st.session_state.get("current_prompt_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})

    prompt_text = prompt_meta.get("prompt", "")
    category = prompt_meta.get("category", "")

    # Randomize display order so position doesn't reveal identity.
    # Store the order so it stays consistent on reruns within this gallery view.
    if "gallery_order" not in st.session_state:
        order = list(results.keys())
        random.shuffle(order)
        st.session_state.gallery_order = order
    display_order = st.session_state.gallery_order

    st.title("Compare Results")
    st.subheader(f'"{prompt_text}"')
    if category:
        st.caption(f"Category: {BIAS_CATEGORIES.get(category, category)}")
    st.markdown("---")

    st.markdown("Browse all images below, then click **Start rating** to evaluate each system.")
    ordered_results = {mk: results[mk] for mk in display_order if mk in results}
    show_gallery(ordered_results)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to exploration", use_container_width=True):
            st.session_state.pop("gallery_order", None)
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
    with col2:
        ratable = [mk for mk in results if results[mk].get("status") in ("success", "refused")]
        if not ratable:
            st.warning("No systems produced results to rate.")
        elif st.button("Start rating", type="primary", use_container_width=True):
            random.shuffle(ratable)
            st.session_state.rating_queue = ratable
            st.session_state.rating_queue_idx = 0
            st.session_state.pop("gallery_order", None)
            st.session_state.current_phase = PHASE_ANNOTATE
            st.rerun()
