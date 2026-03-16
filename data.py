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


def generate_anonymous_id() -> str:
    return f"P-{uuid.uuid4().hex[:8]}"


def save_identity_mapping(anonymous_id: str, real_name: str, background: str):
    """One file per participant to avoid race conditions on a shared file."""
    path = os.path.join(DATA_DIR, f"_id_{anonymous_id}.json")
    _write_json(path, {
        "anonymous_id": anonymous_id,
        "name": real_name,
        "background": background,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    })


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


def generate_images(prompt: str, model_key: str, num_images: int = 4) -> Dict:
    """Returns {"status": "success"|"refused"|"error", "images": [...], "message": ...}.

    Replace the body with actual API calls. See README.md for examples.
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
    """Persist an image locally. Wire into generate_images() when using real APIs."""
    participant_dir = os.path.join(IMAGES_DIR, participant_id)
    os.makedirs(participant_dir, exist_ok=True)
    filepath = os.path.join(participant_dir, f"prompt{prompt_idx}_{model}_{image_idx}.png")
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath


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
