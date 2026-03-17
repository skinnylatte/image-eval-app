"""Run with: streamlit run app.py"""

import streamlit as st
from config import (
    PHASE_WELCOME, PHASE_SHARED, PHASE_EXPLORE,
    PHASE_GALLERY, PHASE_ANNOTATE, PHASE_RESULTS,
    PHASE_FACILITATOR,
)

st.set_page_config(
    page_title="Red Team Image Bias Evaluation",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html('<meta name="robots" content="noindex, nofollow">')

_DEFAULTS = {
    "participant_id": None,
    "participant_display_name": None,
    "participant_background": None,
    "current_phase": PHASE_WELCOME,
    "generated_images": {},
    "prompts": [],
    "current_shared_prompt_idx": 0,
    "shared_prompts_completed": False,
    "current_prompt_results": {},
    "current_prompt_meta": {},
    "scored_models": {},
    "triage_results": {},
    "text_queue": [],
    "text_queue_idx": 0,
    "text_responses": {},
}

for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

_is_facilitator = st.session_state.participant_id == "__facilitator__"
_redirected = False

if not _is_facilitator:
    if st.session_state.current_phase != PHASE_WELCOME and not st.session_state.participant_id:
        st.session_state.current_phase = PHASE_WELCOME
        _redirected = True

    elif st.session_state.current_phase == PHASE_SHARED and st.session_state.shared_prompts_completed:
        st.session_state.current_phase = PHASE_EXPLORE
        _redirected = True

    elif st.session_state.current_phase == PHASE_GALLERY and not st.session_state.current_prompt_results:
        st.session_state.current_phase = PHASE_EXPLORE
        _redirected = True

    elif st.session_state.current_phase == PHASE_ANNOTATE and not st.session_state.scored_models:
        st.session_state.current_phase = PHASE_EXPLORE
        _redirected = True

if _redirected:
    st.rerun()

phase = st.session_state.current_phase

if phase != PHASE_WELCOME and not _is_facilitator and st.session_state.participant_id:
    from data import annotation_count
    from config import PROMPT_TARGET, SHARED_PROMPTS

    with st.sidebar:
        count = annotation_count()
        total_prompts = len(st.session_state.prompts)
        shared_done = st.session_state.shared_prompts_completed
        shared_idx = st.session_state.get("current_shared_prompt_idx", 0)

        # Step indicator
        if not shared_done:
            st.markdown(f"**Step 1 of 2:** Shared prompts ({shared_idx} of {len(SHARED_PROMPTS)})")
        else:
            st.markdown(f"**Step 2 of 2:** Free exploration")
            st.progress(min(total_prompts / PROMPT_TARGET, 1.0),
                        text=f"{total_prompts} of {PROMPT_TARGET} prompts")

        st.caption(f"You've reviewed {count} image sets so far")

        # Warm encouragement
        if count == 0:
            st.markdown("*Your perspective as an expert matters.*")
        elif count < 10:
            st.markdown("*Great start — keep going!*")
        else:
            st.markdown("*Amazing work. You're making a real difference.*")

        # Navigation
        st.markdown("---")
        if not shared_done:
            if st.button("Continue shared prompts", use_container_width=True,
                         disabled=(phase == PHASE_SHARED), type="primary"):
                st.session_state.current_phase = PHASE_SHARED
                st.rerun()
        if st.button("Write a new prompt", use_container_width=True,
                     disabled=(phase in (PHASE_EXPLORE, PHASE_GALLERY, PHASE_ANNOTATE)),
                     type="primary" if shared_done else "secondary"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        if st.button("View my ratings", use_container_width=True,
                     disabled=(phase == PHASE_RESULTS)):
            st.session_state.current_phase = PHASE_RESULTS
            st.rerun()

_PAGES = {
    PHASE_WELCOME: "_1_welcome",
    PHASE_SHARED: "_2_shared_prompts",
    PHASE_EXPLORE: "_3_explore",
    PHASE_GALLERY: "_6_gallery",
    PHASE_ANNOTATE: "_4_annotate",
    PHASE_RESULTS: "_5_results",
    PHASE_FACILITATOR: "_7_facilitator",
}

page_module = _PAGES.get(phase)
if page_module:
    import importlib
    mod = importlib.import_module(f"views.{page_module}")
    mod.run()
else:
    st.error(f"Unknown phase: {phase}")
    st.session_state.current_phase = PHASE_WELCOME
    st.rerun()
