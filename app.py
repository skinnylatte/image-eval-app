"""Run with: streamlit run app.py"""

import streamlit as st
from config import (
    PHASE_WELCOME, PHASE_SHARED, PHASE_EXPLORE,
    PHASE_GALLERY, PHASE_ANNOTATE, PHASE_RESULTS,
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
    "model_group": "A",
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

_redirected = False

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

if phase != PHASE_WELCOME and st.session_state.participant_id:
    from data import annotation_count

    with st.sidebar:
        st.markdown(f"**Participant:** {st.session_state.participant_display_name}")
        st.markdown(f"**Background:** {st.session_state.participant_background}")
        st.markdown(f"**ID:** `{st.session_state.participant_id}`")
        st.markdown("---")
        st.markdown(f"**Annotations:** {annotation_count()}")
        st.markdown(f"**Prompts:** {len(st.session_state.prompts)}")
        st.markdown("---")
        st.markdown("**Need a break?** That's okay. Tell your facilitator.")

        st.markdown("---")
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if phase not in (PHASE_EXPLORE, PHASE_GALLERY, PHASE_ANNOTATE):
                if st.button("Explore", use_container_width=True):
                    st.session_state.current_phase = PHASE_EXPLORE
                    st.rerun()
        with nav_col2:
            if phase != PHASE_RESULTS:
                if st.button("Results", use_container_width=True):
                    st.session_state.current_phase = PHASE_RESULTS
                    st.rerun()

_PAGES = {
    PHASE_WELCOME: "_1_welcome",
    PHASE_SHARED: "_2_shared_prompts",
    PHASE_EXPLORE: "_3_explore",
    PHASE_GALLERY: "_6_gallery",
    PHASE_ANNOTATE: "_4_annotate",
    PHASE_RESULTS: "_5_results",
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
