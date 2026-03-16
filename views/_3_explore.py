from datetime import datetime, timezone

import streamlit as st

from config import BIAS_CATEGORIES, MODELS, PROMPT_TARGET, PHASE_ANNOTATE, PHASE_RESULTS
from data import generate_images, annotation_count
from components import show_image_grid


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

    col_input, col_results = st.columns([1, 2])

    with col_input:
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
        num_images = st.slider("Images per model", 1, 6, 4)
        models_to_test = st.multiselect(
            "Models to test:",
            options=list(MODELS.keys()),
            default=list(MODELS.keys()),
            format_func=lambda k: MODELS[k],
        )

        if st.button("Generate Images", use_container_width=True, type="primary"):
            if not custom_prompt.strip():
                st.error("Please enter a prompt")
            elif not models_to_test:
                st.error("Please select at least one model")
            else:
                prompt_idx = len(st.session_state.prompts)
                for mk in models_to_test:
                    with st.spinner(f"Generating from {MODELS[mk]}..."):
                        result = generate_images(custom_prompt, mk, num_images)
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
                    "models": models_to_test,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                st.rerun()

    with col_results:
        st.subheader("Results")
        prompts = st.session_state.get("prompts", [])
        images = st.session_state.get("generated_images", {})

        if not prompts:
            st.info("Generate images to see results here")
        else:
            for prompt_idx in reversed(range(len(prompts))):
                prompt_data = prompts[prompt_idx]
                st.markdown(f'### "{prompt_data["prompt"]}"')
                st.caption(f"Category: {BIAS_CATEGORIES[prompt_data['category']]}")

                keys = [k for k, v in images.items() if v.get("prompt_idx") == prompt_idx]
                if keys:
                    cols = st.columns(len(keys))
                    for col, key in zip(cols, keys):
                        img_data = images[key]
                        with col:
                            st.markdown(f"**{img_data['model_name']}**")
                            show_image_grid(img_data.get("result", {}), max_per_row=2)
                            if st.button(f"Rate {img_data['model_name']}", key=f"annotate_{key}"):
                                st.session_state.current_phase = PHASE_ANNOTATE
                                st.session_state.current_image_key = key
                                st.rerun()
                st.divider()

    st.markdown("---")
    if st.button("Continue to Analysis"):
        st.session_state.current_phase = PHASE_RESULTS
        st.rerun()
