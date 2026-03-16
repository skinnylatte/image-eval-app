"""
Entry point for the Red Team Image Bias Evaluation app.
Run with: streamlit run app.py
"""

import streamlit as st
from config import PHASE_WELCOME, PHASE_SHARED, PHASE_EXPLORE, PHASE_ANNOTATE, PHASE_RESULTS

st.set_page_config(
    page_title="Red Team Image Bias Evaluation",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "participant_id": None,
    "participant_display_name": None,
    "participant_background": None,
    "current_phase": PHASE_WELCOME,
    "generated_images": {},
    "prompts": [],
    "current_shared_prompt_idx": 0,
    "shared_prompts_completed": False,
}

for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Sidebar (shown when logged in)
# ---------------------------------------------------------------------------

if st.session_state.participant_id:
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

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

phase = st.session_state.current_phase

if phase == PHASE_WELCOME:
    from pages import _1_welcome as page
    page.run()

elif phase == PHASE_SHARED:
    # Guard: don't let participants redo shared prompts
    if st.session_state.shared_prompts_completed:
        st.session_state.current_phase = PHASE_EXPLORE
        st.rerun()
    else:
        from pages import _2_shared_prompts as page
        page.run()

elif phase == PHASE_EXPLORE:
    from pages import _3_explore as page
    page.run()

elif phase == PHASE_ANNOTATE:
    from pages import _4_annotate as page
    page.run()

elif phase == PHASE_RESULTS:
    from pages import _5_results as page
    page.run()

else:
    st.error(f"Unknown phase: {phase}")
    st.session_state.current_phase = PHASE_WELCOME
    st.rerun()
