from datetime import datetime, timezone

import streamlit as st

from config import BIAS_CATEGORIES, BLIND_NAMES, MODELS, PHASE_GALLERY
from data import get_participant_models
from components import generate_with_progress, show_image_grid


def run():
    st.title("Free Exploration")
    st.markdown(
        f"Welcome, **{st.session_state.participant_display_name}** "
        f"({st.session_state.participant_background})"
    )

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
        placeholder="E.g., 'A family celebrating a holiday together'",
        height=100,
    )
    num_images = st.slider("Images per system", 1, 4, 2)

    if st.button("Generate from your systems", use_container_width=True, type="primary"):
        if not custom_prompt.strip():
            st.error("Please enter a prompt")
        else:
            model_keys = get_participant_models()
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

    prompts = st.session_state.get("prompts", [])
    generated = st.session_state.get("generated_images", {})
    if prompts:
        st.markdown("---")
        st.subheader("Previous prompts")
        for i, p in enumerate(reversed(prompts)):
            prompt_idx = len(prompts) - 1 - i
            cat = BIAS_CATEGORIES.get(p["category"], p["category"])
            with st.expander(f"**{cat}:** {p['prompt']}"):
                model_results = {
                    mk: entry["result"]
                    for key, entry in generated.items()
                    if entry.get("prompt_idx") == prompt_idx
                    for mk in [entry["model"]]
                }
                if model_results:
                    cols = st.columns(min(len(model_results), 2))
                    for col, (mk, result) in zip(cols * len(model_results), model_results.items()):
                        with col:
                            st.markdown(f"**{BLIND_NAMES.get(mk, mk)}**")
                            show_image_grid(result, max_per_row=2)
                else:
                    st.caption("Images no longer available")

