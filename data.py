"""
Data layer: save/load annotations, manage participant identity, call image APIs.
Single source of truth for annotation schema.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import streamlit as st

DATA_DIR = "red_team_data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")

for _d in [DATA_DIR, IMAGES_DIR]:
    os.makedirs(_d, exist_ok=True)


# ---------------------------------------------------------------------------
# Participant identity
# ---------------------------------------------------------------------------

def generate_anonymous_id() -> str:
    return f"P-{uuid.uuid4().hex[:8]}"


def save_identity_mapping(anonymous_id: str, real_name: str, background: str):
    """Write one identity file per participant to avoid shared-file race conditions."""
    path = os.path.join(DATA_DIR, f"_id_{anonymous_id}.json")
    _write_json(path, {
        "anonymous_id": anonymous_id,
        "name": real_name,
        "background": background,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    })


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

def build_annotation(
    *,
    prompt: str,
    category: str,
    model_key: str,
    model_name: str,
    prompt_type: str,
    status: str,
    scores: Optional[Dict[str, int]] = None,
    refusal_note: Optional[str] = None,
    expectation: Optional[str] = None,
    authenticity_note: Optional[str] = None,
    harm_note: Optional[str] = None,
) -> Dict:
    """Single place to construct an annotation record."""
    return {
        "participant_id": st.session_state.participant_id,
        "background": st.session_state.participant_background,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_type": prompt_type,
        "prompt": prompt,
        "category": category,
        "model": model_key,
        "model_name": model_name,
        "status": status,
        "scores": scores,
        "refusal_note": refusal_note,
        "expectation": expectation,
        "authenticity_note": authenticity_note,
        "harm_note": harm_note,
    }


def save_annotation(annotation: Dict):
    path = _annotations_path(st.session_state.participant_id)
    existing = _read_json(path, default=[])
    existing.append(annotation)
    _write_json(path, existing)


def load_annotations(participant_id: str) -> List[Dict]:
    return _read_json(_annotations_path(participant_id), default=[])


def annotation_count() -> int:
    return len(load_annotations(st.session_state.participant_id))


def load_all_annotations() -> List[Dict]:
    annotations = []
    for fname in os.listdir(DATA_DIR):
        if fname.endswith("_annotations.json") and not fname.startswith("_"):
            annotations.extend(_read_json(os.path.join(DATA_DIR, fname), default=[]))
    return annotations


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def generate_images(prompt: str, model_key: str, num_images: int = 4) -> Dict:
    """
    Call image generation API.
    Returns {"status": "success"|"refused"|"error", "images": [...], "message": ...}

    PLACEHOLDER — replace the body of this function with actual API calls.

    Example for DALL-E 3:
        import openai
        try:
            resp = openai.images.generate(prompt=prompt, model="dall-e-3", n=num_images, size="1024x1024")
            return {"status": "success", "images": [img.url for img in resp.data], "message": None}
        except openai.BadRequestError as e:
            if "safety" in str(e).lower():
                return {"status": "refused", "images": [], "message": str(e)}
            raise
    """
    return {
        "status": "success",
        "images": [
            f"https://placehold.co/512x512/EEE/999?text={model_key}+{i + 1}"
            for i in range(num_images)
        ],
        "message": None,
    }


def save_image_to_disk(image_bytes: bytes, participant_id: str, prompt_idx: int, model: str, image_idx: int) -> str:
    """Download and persist an image. Call this inside generate_images() once you wire up real APIs."""
    participant_dir = os.path.join(IMAGES_DIR, participant_id)
    os.makedirs(participant_dir, exist_ok=True)
    filepath = os.path.join(participant_dir, f"prompt{prompt_idx}_{model}_{image_idx}.png")
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _annotations_path(participant_id: str) -> str:
    safe_id = participant_id.replace("/", "").replace("\\", "").replace("..", "")
    return os.path.join(DATA_DIR, f"{safe_id}_annotations.json")


def _read_json(path: str, *, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def _write_json(path: str, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
