from datetime import datetime, timezone

import streamlit as st

from config import BIAS_CATEGORIES, MODELS, PROMPT_TARGET, PHASE_GALLERY, PHASE_RESULTS
from data import annotation_count
from components import generate_with_progress


def run():
    st.title("Free Exploration")
    st.markdown(
        f"Welcome, **{st.session_state.participant_display_name}** "
        f"({st.session_state.participant_background})"
    )

    num_prompts = len(st.session_state.get("prompts", []))
    count = annotation_count()
    pct = min(num_prompts / PROMPT_TARGET, 1.0)
    st.progress(pct, text=f"Prompts: {num_prompts} / {PROMPT_TARGET} target | Annotations: {count} total")
    st.markdown("---")

    st.subheader("Write a test prompt")
    st.markdown(
        "Try prompts that test how the systems represent your community. "
        "Think about: professions, celebrations, daily life, beauty standards, "
        "religious practices, political contexts."
    )

    category = st.selectbox(
        "Bias category:",
        options=list(BIAS_CATEGORIES.keys()),
        format_func=lambda k: BIAS_CATEGORIES[k],
    )
    custom_prompt = st.text_area(
        "Your prompt:",
        placeholder="E.g., 'A successful Pakistani businesswoman giving a keynote speech'",
        height=100,
    )
    num_images = st.slider("Images per system", 1, 6, 4)

    if st.button("Generate from all systems", use_container_width=True, type="primary"):
        if not custom_prompt.strip():
            st.error("Please enter a prompt")
        else:
            model_keys = list(MODELS.keys())
            results = generate_with_progress(custom_prompt, model_keys, num_images)

            prompt_idx = len(st.session_state.prompts)
            for mk, result in results.items():
                key = f"{mk}_{prompt_idx}"
                st.session_state.generated_images[key] = {
                    "prompt": custom_prompt,
                    "category": category,
                    "model": mk,
                    "model_name": MODELS[mk],
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "prompt_idx": prompt_idx,
                }
            st.session_state.prompts.append({
                "prompt": custom_prompt,
                "category": category,
                "models": model_keys,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Go to gallery to view and rate
            st.session_state.current_prompt_results = results
            st.session_state.current_prompt_meta = {
                "prompt": custom_prompt,
                "category": category,
                "prompt_type": "free",
            }
            st.session_state.current_phase = PHASE_GALLERY
            st.rerun()

    st.markdown("---")
    if st.button("Continue to Results"):
        st.session_state.current_phase = PHASE_RESULTS
        st.rerun()
