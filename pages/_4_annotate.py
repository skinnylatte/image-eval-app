import streamlit as st

from config import BIAS_CATEGORIES, PHASE_EXPLORE
from data import build_annotation, save_annotation
from components import (
    show_image_grid,
    render_scoring_form,
    render_qualitative_fields,
    render_refusal_field,
    read_scores,
    read_qualitative_fields,
    read_refusal_note,
    validate_annotation,
)


def run():
    st.title("Rate Images")

    if "current_image_key" not in st.session_state:
        st.error("No images selected for annotation")
        if st.button("Back to exploration"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        return

    key = st.session_state.current_image_key
    img_data = st.session_state.generated_images.get(key)

    if not img_data:
        st.error("Image data not found")
        if st.button("Back to exploration"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()
        return

    result = img_data.get("result", {})
    refused = result.get("status") == "refused"

    st.subheader(f"Evaluating: {img_data['model_name']}")
    st.caption(f'Prompt: "{img_data["prompt"]}" | Category: {BIAS_CATEGORIES[img_data["category"]]}')
    st.markdown("---")

    prefix = f"free_{key}"

    if refused:
        render_refusal_field(prefix)
    else:
        show_image_grid(result)
        st.markdown("---")
        st.subheader("Your Evaluation")
        render_scoring_form(prefix)
        st.markdown("---")
        st.subheader("Your Interpretation")
        render_qualitative_fields(prefix)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Back to exploration (without saving)"):
            st.session_state.current_phase = PHASE_EXPLORE
            st.rerun()

    with col2:
        if st.button("Save Annotation", use_container_width=True, type="primary"):
            common = dict(
                prompt=img_data["prompt"],
                category=img_data["category"],
                model_key=img_data["model"],
                model_name=img_data["model_name"],
                prompt_type="free",
            )

            if refused:
                note = read_refusal_note(prefix)
                if not note:
                    st.error("Please explain the significance of this refusal.")
                else:
                    save_annotation(build_annotation(**common, status="refused", refusal_note=note))
                    st.session_state.current_phase = PHASE_EXPLORE
                    st.rerun()
            else:
                scores = read_scores(prefix)
                exp, auth, harm = read_qualitative_fields(prefix)

                if validate_annotation(scores, exp, auth, harm):
                    save_annotation(build_annotation(
                        **common, status="success", scores=scores,
                        expectation=exp, authenticity_note=auth, harm_note=harm,
                    ))
                    st.session_state.current_phase = PHASE_EXPLORE
                    st.rerun()
