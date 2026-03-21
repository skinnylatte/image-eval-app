import streamlit as st
from config import SHARED_PROMPTS, BIAS_CATEGORIES, PHASE_EXPLORE, PHASE_GALLERY
from data import get_participant_models
from components import generate_with_progress


def run():
    st.title("Shared Prompts")
    st.markdown(f"Welcome, **{st.session_state.participant_display_name}**")
    st.markdown("---")
    st.markdown(
        "Before you explore freely, everyone rates the **same 5 prompts**. "
        "This lets us compare how different people experience the same images."
    )

    idx = st.session_state.get("current_shared_prompt_idx", 0)

    if idx >= len(SHARED_PROMPTS):
        st.success("You've completed all shared prompts.")
        st.session_state.shared_prompts_completed = True
        if st.button("Continue to test your ideas", type="primary"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        return

    shared = SHARED_PROMPTS[idx]
    prompt, category = shared["prompt"], shared["category"]
    models = get_participant_models()

    st.progress(idx / len(SHARED_PROMPTS), text=f"Shared prompt {idx + 1} of {len(SHARED_PROMPTS)}")
    st.subheader(f'Prompt: "{prompt}"')
    st.caption(f"Category: {BIAS_CATEGORIES[category]}")

    st.caption("This will take 10-30 seconds. You'll then compare the results from all 4 systems.")
    if st.button("Generate images", type="primary", use_container_width=True):
        results = generate_with_progress(prompt, models)

        st.session_state.current_prompt_results = results
        st.session_state.current_prompt_meta = {
            "prompt": prompt,
            "category": category,
            "prompt_type": "shared",
            "shared_prompt_idx": idx,
        }
        st.session_state.current_phase = PHASE_GALLERY
        st.rerun()
