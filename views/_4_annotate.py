import streamlit as st

from config import BLIND_NAMES, MODELS, PHASE_EXPLORE, PHASE_SHARED, PHASE_GALLERY
from data import build_annotation, save_annotation
from components import show_image_grid, render_qualitative_fields, read_qualitative_fields, validate_text_fields


def run():
    text_queue = st.session_state.get("text_queue", [])
    idx = st.session_state.get("text_queue_idx", 0)
    results = st.session_state.get("current_prompt_results", {})
    prompt_meta = st.session_state.get("current_prompt_meta", {})
    scored_models = st.session_state.get("scored_models", {})

    if not text_queue or idx >= len(text_queue):
        _save_all_and_advance()
        return

    mk = text_queue[idx]
    blind_name = BLIND_NAMES[mk]
    result = results.get(mk, {})
    scores = scored_models.get(mk, {}).get("scores", {})
    prompt_text = prompt_meta.get("prompt", "")

    st.title(f"Tell us about {blind_name}")
    st.progress(idx / len(text_queue), text=f"System {idx + 1} of {len(text_queue)}")
    st.caption(f'Prompt: "{prompt_text}"')
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        show_image_grid(result, max_per_row=2)
    with col2:
        st.markdown(f"**Your scores for {blind_name}:**")
        st.markdown(f"- Authenticity: **{scores.get('authenticity', '?')}**/5")
        st.markdown(f"- Diversity: **{scores.get('diversity', '?')}**/5")
        st.markdown(f"- Respectfulness: **{scores.get('respectfulness', '?')}**/5")

    st.markdown("---")
    prefix = f"text_{idx}_{mk}"
    render_qualitative_fields(prefix)

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Back to scoring"):
            st.session_state.current_phase = PHASE_GALLERY
            st.rerun()
    with col2:
        is_last = idx == len(text_queue) - 1
        btn_label = "Save and finish" if is_last else "Save and next"

        if st.button(btn_label, type="primary", use_container_width=True):
            exp, auth, harm = read_qualitative_fields(prefix)
            if validate_text_fields(exp, auth, harm):
                st.session_state.setdefault("text_responses", {})[mk] = {
                    "expectation": exp,
                    "authenticity_note": auth,
                    "harm_note": harm,
                }
                if is_last:
                    _save_all_and_advance()
                else:
                    st.session_state.text_queue_idx = idx + 1
                    st.rerun()


def _save_all_and_advance():
    scored_models = st.session_state.get("scored_models", {})
    text_responses = st.session_state.get("text_responses", {})
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

        if data["status"] == "refused":
            save_annotation(build_annotation(**common, status="refused", refusal_note=data["refusal_note"]))
        else:
            texts = text_responses.get(mk, {})
            save_annotation(build_annotation(
                **common, status="success", scores=data["scores"],
                expectation=texts.get("expectation"),
                authenticity_note=texts.get("authenticity_note"),
                harm_note=texts.get("harm_note"),
            ))

    st.session_state.scored_models = {}
    st.session_state.text_responses = {}
    st.session_state.text_queue = []
    st.session_state.text_queue_idx = 0

    if prompt_meta.get("prompt_type") == "shared":
        st.session_state.current_shared_prompt_idx = prompt_meta.get("shared_prompt_idx", 0) + 1
        st.session_state.current_phase = PHASE_SHARED
    else:
        st.session_state.current_phase = PHASE_EXPLORE

    st.rerun()
