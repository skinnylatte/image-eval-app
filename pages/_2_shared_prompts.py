import streamlit as st
from config import SHARED_PROMPTS, MODELS, BIAS_CATEGORIES, PHASE_EXPLORE
from data import generate_images, build_annotation, save_annotation
from components import (
    show_model_comparison,
    render_scoring_form,
    render_qualitative_fields,
    render_refusal_field,
    read_scores,
    read_qualitative_fields,
    read_refusal_note,
    validate_annotation,
)


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
        st.success("You've completed all shared prompts. Moving to free exploration.")
        st.session_state.shared_prompts_completed = True
        st.session_state.current_phase = PHASE_EXPLORE
        st.rerun()
        return

    shared = SHARED_PROMPTS[idx]
    prompt, category = shared["prompt"], shared["category"]
    models = list(MODELS.keys())

    st.progress(idx / len(SHARED_PROMPTS), text=f"Shared prompt {idx + 1} of {len(SHARED_PROMPTS)}")
    st.subheader(f'Prompt: "{prompt}"')
    st.caption(f"Category: {BIAS_CATEGORIES[category]}")

    # Generate step
    gen_key = f"shared_{idx}_results"
    if gen_key not in st.session_state:
        if st.button("Generate images from all models", type="primary", use_container_width=True):
            results = {}
            for mk in models:
                with st.spinner(f"Generating from {MODELS[mk]}..."):
                    results[mk] = generate_images(prompt, mk)
            st.session_state[gen_key] = results
            st.rerun()
        return

    results = st.session_state[gen_key]
    show_model_comparison(results)
    st.markdown("---")

    # Annotation form for each model
    st.subheader("Rate each model")

    for mk in models:
        result = results.get(mk, {})
        with st.expander(f"Rate: {MODELS[mk]}", expanded=True):
            prefix = f"shared_{idx}_{mk}"
            if result.get("status") == "refused":
                render_refusal_field(prefix)
            else:
                render_scoring_form(prefix)
                render_qualitative_fields(prefix)

    if st.button("Save ratings and continue", type="primary", use_container_width=True):
        # Validate ALL models first, then save. Never save partial results.
        all_valid = True
        pending = []

        for mk in models:
            result = results.get(mk, {})
            prefix = f"shared_{idx}_{mk}"

            if result.get("status") == "refused":
                note = read_refusal_note(prefix)
                if not note:
                    st.error(f"Please explain the significance of {MODELS[mk]}'s refusal.")
                    all_valid = False
                else:
                    pending.append(build_annotation(
                        prompt=prompt, category=category, model_key=mk,
                        model_name=MODELS[mk], prompt_type="shared",
                        status="refused", refusal_note=note,
                    ))
            else:
                scores = read_scores(prefix)
                exp, auth, harm = read_qualitative_fields(prefix)

                if not validate_annotation(scores, exp, auth, harm):
                    all_valid = False
                else:
                    pending.append(build_annotation(
                        prompt=prompt, category=category, model_key=mk,
                        model_name=MODELS[mk], prompt_type="shared",
                        status="success", scores=scores,
                        expectation=exp, authenticity_note=auth, harm_note=harm,
                    ))

        if all_valid:
            for ann in pending:
                save_annotation(ann)
            st.session_state.current_shared_prompt_idx = idx + 1
            st.rerun()
