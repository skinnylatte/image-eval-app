import streamlit as st

from config import BLIND_NAMES, MODELS, PHASE_EXPLORE, PHASE_SHARED, PHASE_GALLERY
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
    queue = st.session_state.get("rating_queue", [])
    idx = st.session_state.get("rating_queue_idx", 0)
    results = st.session_state.get("current_prompt_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})

    if not queue or idx >= len(queue):
        st.session_state.current_phase = PHASE_EXPLORE
        st.rerun()
        return

    mk = queue[idx]
    blind_name = BLIND_NAMES[mk]
    result = results.get(mk, {})
    refused = result.get("status") == "refused"
    prompt_text = prompt_meta.get("prompt", "")
    category = prompt_meta.get("category", "")

    st.title(f"Rate: {blind_name}")
    st.progress(idx / len(queue), text=f"System {idx + 1} of {len(queue)}")
    st.caption(f'Prompt: "{prompt_text}"')
    st.markdown("---")

    prefix = f"rate_{idx}_{mk}"

    if refused:
        render_refusal_field(prefix)
    else:
        show_image_grid(result)
        st.markdown("---")
        render_scoring_form(prefix)
        st.markdown("---")
        render_qualitative_fields(prefix)

    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Back to gallery"):
            st.session_state.current_phase = PHASE_GALLERY
            st.rerun()
    with col2:
        is_last = idx == len(queue) - 1
        btn_label = "Save and finish" if is_last else "Save and next"

        if st.button(btn_label, type="primary", use_container_width=True):
            common = dict(
                prompt=prompt_text,
                category=category,
                model_key=mk,
                model_name=MODELS[mk],
                blind_name=blind_name,
                prompt_type=prompt_meta.get("prompt_type", "free"),
            )

            if refused:
                note = read_refusal_note(prefix)
                if not note:
                    st.error("Please explain the significance of this refusal.")
                else:
                    save_annotation(build_annotation(**common, status="refused", refusal_note=note))
                    _advance()
            else:
                scores = read_scores(prefix)
                exp, auth, harm = read_qualitative_fields(prefix)
                if validate_annotation(scores, exp, auth, harm):
                    save_annotation(build_annotation(
                        **common, status="success", scores=scores,
                        expectation=exp, authenticity_note=auth, harm_note=harm,
                    ))
                    _advance()


def _advance():
    idx = st.session_state.rating_queue_idx
    queue = st.session_state.rating_queue
    meta = st.session_state.get("current_prompt_meta", {})

    if idx + 1 >= len(queue):
        st.session_state.rating_queue = []
        st.session_state.rating_queue_idx = 0

        if meta.get("prompt_type") == "shared":
            # Advance to next shared prompt
            st.session_state.current_shared_prompt_idx = meta.get("shared_prompt_idx", 0) + 1
            st.session_state.current_phase = PHASE_SHARED
        else:
            st.session_state.current_phase = PHASE_EXPLORE
    else:
        st.session_state.rating_queue_idx = idx + 1

    st.rerun()
