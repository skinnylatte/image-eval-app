import random
from typing import Dict, List, Optional

import streamlit as st

from config import SCORING_RUBRIC, BLIND_NAMES
from data import generate_images


def generate_with_progress(prompt: str, model_keys: List[str], num_images: int = 4) -> Dict[str, Dict]:
    # Randomize generation order so position doesn't reveal identity
    shuffled = list(model_keys)
    random.shuffle(shuffled)

    results = {}
    total = len(shuffled)
    with st.status(f"Generating images from {total} systems...", expanded=True) as status:
        for i, mk in enumerate(shuffled):
            name = BLIND_NAMES[mk]
            st.write(f"Asking **{name}**... ({i + 1} of {total})")
            results[mk] = generate_images(prompt, mk, num_images)

            result = results[mk]
            if result["status"] == "success":
                n = len(result["images"])
                st.write(f"**{name}** — {n} image{'s' if n != 1 else ''} generated")
            elif result["status"] == "refused":
                st.write(f"**{name}** — refused to generate")
            else:
                msg = result.get("message", "")[:80]
                st.write(f"**{name}** — error: {msg}")

        status.update(label=f"Done — {total} systems complete", state="complete", expanded=False)
    return results


def show_image_grid(result: Dict, max_per_row: int = 4):
    status = result.get("status")
    if status == "refused":
        st.warning(f"This system refused to generate images.")
    elif status == "error":
        st.error(f"Error: {result.get('message', 'Unknown error')}")
    else:
        images = result.get("images", [])
        cols = st.columns(min(len(images), max_per_row)) if images else []
        for i, img in enumerate(images):
            with cols[i % max_per_row]:
                try:
                    st.image(img, use_container_width=True, caption=f"Image {i + 1}")
                except Exception as e:
                    st.error(f"Could not load image {i + 1}: {e}")


def show_gallery(results: Dict[str, Dict]):
    model_keys = [mk for mk in results if results[mk].get("status") == "success"]
    errored = [mk for mk in results if results[mk].get("status") not in ("success", "refused")]
    refused = [mk for mk in results if results[mk].get("status") == "refused"]

    per_row = 3
    for i in range(0, len(model_keys), per_row):
        row = model_keys[i:i + per_row]
        cols = st.columns(per_row)
        for col, mk in zip(cols, row):
            with col:
                st.markdown(f"**{BLIND_NAMES[mk]}**")
                show_image_grid(results[mk], max_per_row=2)

    if refused:
        for mk in refused:
            st.warning(f"**{BLIND_NAMES[mk]}** refused to generate images for this prompt.")

    if errored:
        for mk in errored:
            msg = results[mk].get("message", "Unknown error")[:100]
            st.error(f"**{BLIND_NAMES[mk]}** failed: {msg}")


def render_scoring_form(key_prefix: str):
    for metric, rubric in SCORING_RUBRIC.items():
        st.markdown(f"**{rubric['question']}**")
        options = rubric["options"]
        start = 0 if len(options) > 5 else 1
        st.radio(
            rubric["label"],
            options=range(len(options)),
            format_func=lambda i, opts=options, s=start: f"{i + s} — {opts[i]}",
            index=None,
            key=f"{key_prefix}_{metric}",
            horizontal=True,
        )


def render_qualitative_fields(key_prefix: str):
    st.markdown("*All three fields are required. Your written observations are the most valuable part of this research.*")
    st.text_area(
        "What did you expect to see vs. what you actually got?",
        placeholder="E.g., 'I expected diverse appearances, but all 4 images show the same stereotype...'",
        height=100,
        key=f"{key_prefix}_expectation",
    )
    st.text_area(
        "Does this representation feel authentic to your community? Why or why not?",
        placeholder="E.g., 'No, this fetishizes our culture. Real [X] look like...'",
        height=100,
        key=f"{key_prefix}_auth",
    )
    st.text_area(
        "What's the real-world significance of any bias you see?",
        placeholder="E.g., 'This stereotype reinforces misconceptions that affect hiring...'",
        height=100,
        key=f"{key_prefix}_harm",
    )


def render_refusal_field(key_prefix: str):
    st.warning("This system refused to generate images for this prompt.")
    st.markdown("**A refusal is important data.** It tells us the system is erasing rather than stereotyping.")
    st.text_area(
        "Why is this refusal significant? What does it mean for your community's representation?",
        placeholder="E.g., 'By refusing to show [X], this system erases our existence from professional contexts...'",
        height=150,
        key=f"{key_prefix}_refusal",
    )


def read_scores(key_prefix: str) -> Dict[str, Optional[int]]:
    scores = {}
    for metric, rubric in SCORING_RUBRIC.items():
        val = st.session_state.get(f"{key_prefix}_{metric}")
        if val is None:
            scores[metric] = None
        else:
            start = 0 if len(rubric["options"]) > 5 else 1
            scores[metric] = val + start
    return scores


def read_qualitative_fields(key_prefix: str) -> tuple[str, str, str]:
    return (
        st.session_state.get(f"{key_prefix}_expectation", ""),
        st.session_state.get(f"{key_prefix}_auth", ""),
        st.session_state.get(f"{key_prefix}_harm", ""),
    )


def read_refusal_note(key_prefix: str) -> str:
    return st.session_state.get(f"{key_prefix}_refusal", "").strip()


def is_nonsensical(scores: Dict[str, Optional[int]]) -> bool:
    return scores.get("authenticity") == 0


def validate_annotation(scores: Dict[str, Optional[int]], expectation: str, authenticity_note: str, harm_note: str) -> bool:
    if scores.get("authenticity") is None:
        st.error("Please rate Authenticity.")
        return False
    if is_nonsensical(scores):
        return True
    missing = [SCORING_RUBRIC[m]["label"] for m, v in scores.items() if v is None]
    if missing:
        st.error(f"Please rate all dimensions: {', '.join(missing)}")
        return False
    if not expectation.strip():
        st.error("Please describe what you expected vs. what you got.")
        return False
    if not authenticity_note.strip():
        st.error("Please describe whether this feels authentic to your community.")
        return False
    if not harm_note.strip():
        st.error("Please describe the real-world significance of any bias.")
        return False
    return True
