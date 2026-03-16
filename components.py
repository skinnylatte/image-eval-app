"""
Reusable Streamlit UI components.
"""

from typing import Dict, Optional

import streamlit as st

from config import SCORING_RUBRIC, MODELS


# ---------------------------------------------------------------------------
# Image display
# ---------------------------------------------------------------------------

def show_image_grid(result: Dict, max_per_row: int = 4):
    """Display images from an API result dict, handling refusals/errors."""
    status = result.get("status")
    if status == "refused":
        st.warning(f"Model refused: {result.get('message', 'No reason given')}")
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


def show_model_comparison(results: Dict[str, Dict]):
    """Show results from multiple models side by side."""
    model_keys = list(results.keys())
    cols = st.columns(len(model_keys))
    for col, key in zip(cols, model_keys):
        with col:
            st.markdown(f"**{MODELS[key]}**")
            show_image_grid(results[key], max_per_row=2)


# ---------------------------------------------------------------------------
# Scoring form
# ---------------------------------------------------------------------------

def render_scoring_form(key_prefix: str):
    """
    Render radio-button scoring for all rubric dimensions.
    Scores are stored in st.session_state under {key_prefix}_{metric}.
    Use read_scores() to retrieve them.
    """
    for metric, rubric in SCORING_RUBRIC.items():
        st.markdown(f"**{rubric['question']}**")
        options = rubric["options"]
        st.radio(
            rubric["label"],
            options=range(len(options)),
            format_func=lambda i, opts=options: f"{i + 1} — {opts[i]}",
            index=None,
            key=f"{key_prefix}_{metric}",
            horizontal=True,
        )


def render_qualitative_fields(key_prefix: str):
    """
    Render the three required text fields.
    Values are stored in st.session_state under {key_prefix}_expectation, _auth, _harm.
    Use read_qualitative_fields() to retrieve them.
    """
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
    """
    Render text field for model refusal annotation.
    Value stored in st.session_state under {key_prefix}_refusal.
    """
    st.warning("This model refused to generate images for this prompt.")
    st.markdown("**A refusal is important data.** It tells us the system is erasing rather than stereotyping.")
    st.text_area(
        "Why is this refusal significant? What does it mean for your community's representation?",
        placeholder="E.g., 'By refusing to show [X], this model erases our existence from professional contexts...'",
        height=150,
        key=f"{key_prefix}_refusal",
    )


# ---------------------------------------------------------------------------
# Reading values back from session state
# ---------------------------------------------------------------------------

def read_scores(key_prefix: str) -> Dict[str, Optional[int]]:
    """Read scores from session state. Returns {metric: 1-5 or None}."""
    scores = {}
    for metric in SCORING_RUBRIC:
        val = st.session_state.get(f"{key_prefix}_{metric}")
        scores[metric] = (val + 1) if val is not None else None
    return scores


def read_qualitative_fields(key_prefix: str) -> tuple[str, str, str]:
    """Read qualitative text from session state. Returns (expectation, auth, harm)."""
    return (
        st.session_state.get(f"{key_prefix}_expectation", ""),
        st.session_state.get(f"{key_prefix}_auth", ""),
        st.session_state.get(f"{key_prefix}_harm", ""),
    )


def read_refusal_note(key_prefix: str) -> str:
    """Read refusal note from session state."""
    return st.session_state.get(f"{key_prefix}_refusal", "").strip()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_annotation(scores: Dict[str, Optional[int]], expectation: str, authenticity_note: str, harm_note: str) -> bool:
    """Validate that a complete annotation has been provided. Shows errors and returns True if valid."""
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
