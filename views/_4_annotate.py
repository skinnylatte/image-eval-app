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
    validate_scores_only,
    validate_text_fields,
)


def run():
    text_queue = st.session_state.get("text_queue", [])
    idx = st.session_state.get("text_queue_idx", 0)
    results = st.session_state.get("current_prompt_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})

    if not text_queue or idx >= len(text_queue):
        _save_all_and_advance()
        return

    mk = text_queue[idx]
    blind_name = BLIND_NAMES[mk]
    result = results.get(mk, {})
    refused = result.get("status") == "refused"
    prompt_text = prompt_meta.get("prompt", "")
    prompt_type = prompt_meta.get("prompt_type", "free")

    st.title(f"Tell us about {blind_name}")
    st.progress(idx / len(text_queue), text=f"System {idx + 1} of {len(text_queue)}")
    if refused:
        st.info(f"This system refused to generate images for: \"{prompt_text}\"")
    else:
        st.info(f"You marked this system as problematic for: \"{prompt_text}\"")
    st.markdown("---")

    prefix = f"deepdive_{idx}_{mk}"

    if refused:
        render_refusal_field(prefix)
    else:
        show_image_grid(result, max_per_row=2)
        st.markdown("---")
        st.markdown("**Score this system:**")
        render_scoring_form(prefix, prompt_type)
        st.markdown("---")
        render_qualitative_fields(prefix, prompt_type)

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("← Back to rating images"):
            st.session_state.current_phase = PHASE_GALLERY
            st.rerun()
    with col2:
        is_last = idx == len(text_queue) - 1
        btn_label = "Save and finish" if is_last else "Save and next"

        if st.button(btn_label, type="primary", use_container_width=True):
            if refused:
                note = read_refusal_note(prefix)
                if not note:
                    st.error("Please explain the significance of this refusal.")
                else:
                    st.session_state.scored_models[mk] = {"status": "refused", "refusal_note": note}
                    st.session_state.setdefault("text_responses", {})[mk] = {}
                    _next_or_finish(is_last)
            else:
                scores = read_scores(prefix)
                if not validate_scores_only(scores):
                    return
                exp, auth, harm = read_qualitative_fields(prefix, prompt_type)
                if not validate_text_fields(exp, auth, harm, prompt_type):
                    return
                st.session_state.scored_models[mk] = {"status": "success", "scores": scores}
                st.session_state.setdefault("text_responses", {})[mk] = {
                    "expectation": exp,
                    "authenticity_note": auth,
                    "harm_note": harm,
                }
                _next_or_finish(is_last)


def _next_or_finish(is_last: bool):
    if is_last:
        _save_all_and_advance()
    else:
        st.session_state.text_queue_idx += 1
        st.rerun()


def _save_all_and_advance():
    scored_models = st.session_state.get("scored_models", {})
    text_responses = st.session_state.get("text_responses", {})
    triage_results = st.session_state.get("triage_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})
    prompt_text = prompt_meta.get("prompt", "")
    category = prompt_meta.get("category", "")
    prompt_type = prompt_meta.get("prompt_type", "free")

    for mk, data in scored_models.items():
        blind_name = BLIND_NAMES[mk]
        common = dict(
            prompt=prompt_text,
            category=category,
            model_key=mk,
            model_name=MODELS[mk],
            blind_name=blind_name,
            prompt_type=prompt_type,
        )

        triage_label = triage_results.get(mk, "")
        texts = text_responses.get(mk, {})

        if data["status"] == "refused":
            save_annotation(build_annotation(
                **common, status="refused",
                refusal_note=data.get("refusal_note", ""),
            ))
        else:
            save_annotation(build_annotation(
                **common, status="success",
                scores=data["scores"],
                expectation=texts.get("expectation"),
                authenticity_note=texts.get("authenticity_note"),
                harm_note=texts.get("harm_note"),
            ))

    st.session_state.scored_models = {}
    st.session_state.text_responses = {}
    st.session_state.triage_results = {}
    st.session_state.text_queue = []
    st.session_state.text_queue_idx = 0

    if prompt_meta.get("prompt_type") == "shared":
        st.session_state.current_shared_prompt_idx = prompt_meta.get("shared_prompt_idx", 0) + 1
        st.session_state.current_phase = PHASE_SHARED
    else:
        st.session_state.current_phase = PHASE_EXPLORE

    st.rerun()
