import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import openai
import requests
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


# ---------------------------------------------------------------------------
# Image generation — dispatch + per-model implementations
# ---------------------------------------------------------------------------

_GENERATORS = {}


def _generator(model_key):
    def decorator(fn):
        _GENERATORS[model_key] = fn
        return fn
    return decorator


def generate_images(prompt: str, model_key: str, num_images: int = 4) -> Dict:
    """Returns {"status": "success"|"refused"|"error", "images": [...], "message": ...}."""
    gen = _GENERATORS.get(model_key)
    if not gen:
        return {"status": "error", "images": [], "message": f"Unknown model: {model_key}"}
    try:
        return gen(prompt, num_images)
    except Exception as e:
        return {"status": "error", "images": [], "message": str(e)}


def _require_env(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        raise EnvironmentError(f"{var} not set")
    return val


@_generator("dalle")
def _generate_dalle(prompt: str, num_images: int) -> Dict:
    client = openai.OpenAI(api_key=_require_env("OPENAI_API_KEY"))
    images = []
    for _ in range(num_images):
        try:
            resp = client.images.generate(prompt=prompt, model="dall-e-3", n=1, size="1024x1024")
            images.append(resp.data[0].url)
        except openai.BadRequestError as e:
            if "safety" in str(e).lower() or "policy" in str(e).lower():
                return {"status": "refused", "images": [], "message": str(e)}
            raise
    return {"status": "success", "images": images, "message": None}


@_generator("stable_diffusion")
def _generate_stable_diffusion(prompt: str, num_images: int) -> Dict:
    api_url = "https://router.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {_require_env('HF_API_TOKEN')}"}
    images = []
    for _ in range(num_images):
        resp = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=60)
        if resp.status_code == 200:
            images.append(resp.content)
        elif resp.status_code == 400:
            return {"status": "refused", "images": [], "message": resp.text}
        else:
            return {"status": "error", "images": [], "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    return {"status": "success", "images": images, "message": None}


@_generator("flux")
def _generate_flux(prompt: str, num_images: int) -> Dict:
    import replicate as replicate_client
    os.environ["REPLICATE_API_TOKEN"] = _require_env("REPLICATE_API_TOKEN")
    images = []
    for _ in range(num_images):
        output = replicate_client.run(
            "black-forest-labs/flux-1.1-pro",
            input={"prompt": prompt, "aspect_ratio": "1:1"},
        )
        if isinstance(output, str):
            images.append(output)
        elif hasattr(output, '__iter__'):
            images.extend(output)
    return {"status": "success", "images": images, "message": None}


@_generator("imagen")
def _generate_imagen(prompt: str, num_images: int) -> Dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_require_env("GOOGLE_API_KEY"))
    capped = min(num_images, 4)  # Imagen 4 max is 4 per request
    resp = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=capped),
    )
    if not resp.generated_images:
        return {"status": "refused", "images": [], "message": "No images returned (likely safety filter)"}

    images = []
    for img in resp.generated_images:
        images.append(img.image._pil_image)  # PIL Image — st.image() handles these
    return {"status": "success", "images": images, "message": None}


@_generator("qwen")
def _generate_qwen(prompt: str, num_images: int) -> Dict:
    api_key = _require_env("DASHSCOPE_API_KEY")
    api_url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": "wanx-v1",
        "input": {"prompt": prompt},
        "parameters": {"n": min(num_images, 4), "size": "1024*1024"},
    }

    # Submit task
    resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        return {"status": "error", "images": [], "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    task_id = resp.json().get("output", {}).get("task_id")
    if not task_id:
        return {"status": "error", "images": [], "message": "No task_id returned"}

    # Poll for results
    import time
    status_url = f"https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
    for _ in range(60):
        time.sleep(2)
        status_resp = requests.get(status_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        result = status_resp.json()
        task_status = result.get("output", {}).get("task_status")

        if task_status == "SUCCEEDED":
            results = result.get("output", {}).get("results", [])
            images = [r["url"] for r in results if r.get("url")]
            return {"status": "success", "images": images, "message": None}
        elif task_status == "FAILED":
            msg = result.get("output", {}).get("message", "Unknown error")
            if "content" in msg.lower() or "safety" in msg.lower():
                return {"status": "refused", "images": [], "message": msg}
            return {"status": "error", "images": [], "message": msg}

    return {"status": "error", "images": [], "message": "Timed out waiting for Qwen"}



@_generator("hunyuan")
def _generate_hunyuan(prompt: str, num_images: int) -> Dict:
    """Hunyuan via Replicate (easiest access, no Tencent Cloud account needed)."""
    import replicate as replicate_client
    os.environ["REPLICATE_API_TOKEN"] = _require_env("REPLICATE_API_TOKEN")
    images = []
    for _ in range(num_images):
        output = replicate_client.run(
            "tencent/hunyuan-image-3",
            input={"prompt": prompt, "width": 1024, "height": 1024},
        )
        if isinstance(output, str):
            images.append(output)
        elif hasattr(output, '__iter__'):
            images.extend(output)
    return {"status": "success", "images": images, "message": None}


# ---------------------------------------------------------------------------
# Image persistence
# ---------------------------------------------------------------------------

def save_image_to_disk(image_bytes: bytes, participant_id: str, prompt_idx: int, model: str, image_idx: int) -> str:
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
