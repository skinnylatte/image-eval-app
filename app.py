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

    elif st.session_state.current_phase == PHASE_GALLERY and not st.session_state.current_prompt_results:
        st.session_state.current_phase = PHASE_EXPLORE
        _redirected = True

    elif st.session_state.current_phase == PHASE_ANNOTATE and not st.session_state.scored_models and not st.session_state.text_queue:
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

        in_active_task = phase in (PHASE_GALLERY, PHASE_ANNOTATE)

        # Shared prompts
        if phase == PHASE_SHARED:
            st.markdown("● **Shared prompts**")
            st.progress(shared_idx / len(SHARED_PROMPTS),
                        text=f"{shared_idx} of {len(SHARED_PROMPTS)}")
        elif in_active_task:
            st.markdown("✓ Shared prompts" if shared_done else "○ Shared prompts")
        else:
            label = "✓ Shared prompts" if shared_done else "○ Shared prompts"
            if st.button(label, use_container_width=True, key="nav_shared"):
                st.session_state.current_phase = PHASE_SHARED
                st.rerun()

        # Test your ideas
        if phase == PHASE_EXPLORE:
            st.markdown("● **Test your ideas**")
            st.progress(min(total_prompts / PROMPT_TARGET, 1.0),
                        text=f"{total_prompts} of {PROMPT_TARGET}")
        elif in_active_task:
            explore_done = total_prompts >= PROMPT_TARGET
            st.markdown("✓ Test your ideas" if explore_done else "○ Test your ideas")
        else:
            explore_done = total_prompts >= PROMPT_TARGET
            label = "✓ Test your ideas" if explore_done else "○ Test your ideas"
            if st.button(label, use_container_width=True, key="nav_explore"):
                st.session_state.current_phase = PHASE_EXPLORE
                st.rerun()

        # Your results
        if phase == PHASE_RESULTS:
            st.markdown("● **Your results**")
        elif in_active_task:
            st.markdown("○ Your results")
        else:
            if st.button("○ Your results", use_container_width=True, key="nav_results"):
                st.session_state.current_phase = PHASE_RESULTS
                st.rerun()

        st.markdown("---")
        if in_active_task:
            st.warning("Finish rating images to navigate away.")
        elif count == 0:
            st.caption("Your perspective as an expert matters.")
        elif count < 10:
            st.caption(f"{count} image sets reviewed · Great start!")
        else:
            st.caption(f"{count} image sets reviewed · Amazing work.")

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

st.markdown("---")
st.caption("A project of [Future Ethics](https://futureethics.ai)")
