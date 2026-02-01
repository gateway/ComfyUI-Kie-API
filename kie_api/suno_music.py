"""KIE Suno music generation helper (v1 create-only)."""

import json
from typing import Any

from .auth import _load_api_key
from .http import TransientKieError, requests
from .log import _log

GENERATE_URL = "https://api.kie.ai/api/v1/generate"
MODEL_OPTIONS = ["V4", "V4_5", "V4_5PLUS", "V4_5ALL", "V5"]
VOCAL_GENDER_OPTIONS = ["m", "f"]


def _validate_length(field_name: str, value: str | None, max_len: int) -> None:
    if value is None:
        return
    if len(value) > max_len:
        raise RuntimeError(f"{field_name} exceeds max length of {max_len} characters.")


def _max_prompt_len(model: str) -> int:
    return 3000 if model == "V4" else 5000


def _max_style_len(model: str) -> int:
    return 200 if model == "V4" else 1000


def run_suno_generate(
    *,
    prompt: str,
    custom_mode: bool,
    instrumental: bool,
    model: str,
    callback_url: str,
    style: str | None = None,
    title: str | None = None,
    negative_tags: str | None = None,
    vocal_gender: str | None = None,
    style_weight: float | None = None,
    weirdness_constraint: float | None = None,
    audio_weight: float | None = None,
    persona_id: str | None = None,
    log: bool = True,
) -> tuple[str, str]:
    """Create a Suno music generation task. Returns (task_id, raw_json)."""
    if model not in MODEL_OPTIONS:
        raise RuntimeError("Invalid model. Use the pinned enum options.")
    if vocal_gender and vocal_gender not in VOCAL_GENDER_OPTIONS:
        raise RuntimeError("vocal_gender must be 'm' or 'f'.")
    if not callback_url:
        raise RuntimeError("callback_url is required by the API spec.")

    prompt_text = (prompt or "").strip()
    style_text = (style or "").strip()
    title_text = (title or "").strip()

    if custom_mode:
        if not style_text:
            raise RuntimeError("style is required when custom_mode is enabled.")
        if not title_text:
            raise RuntimeError("title is required when custom_mode is enabled.")
        if not instrumental and not prompt_text:
            raise RuntimeError("prompt (lyrics) is required when custom_mode is enabled and instrumental is false.")
        _validate_length("prompt", prompt_text, _max_prompt_len(model))
        _validate_length("style", style_text, _max_style_len(model))
        _validate_length("title", title_text, 80)
    else:
        if not prompt_text:
            raise RuntimeError("prompt is required when custom_mode is disabled.")
        _validate_length("prompt", prompt_text, 500)
        # Spec says other fields should be empty in non-custom mode.
        if any([style_text, title_text, negative_tags, vocal_gender, persona_id]):
            raise RuntimeError("style/title/negative_tags/vocal_gender/persona_id must be empty when custom_mode is false.")

    payload: dict[str, Any] = {
        "prompt": prompt_text,
        "customMode": bool(custom_mode),
        "instrumental": bool(instrumental),
        "model": model,
        "callBackUrl": callback_url,
    }
    if style_text:
        payload["style"] = style_text
    if title_text:
        payload["title"] = title_text
    if negative_tags:
        payload["negativeTags"] = negative_tags
    if vocal_gender:
        payload["vocalGender"] = vocal_gender
    if style_weight is not None:
        payload["styleWeight"] = style_weight
    if weirdness_constraint is not None:
        payload["weirdnessConstraint"] = weirdness_constraint
    if audio_weight is not None:
        payload["audioWeight"] = audio_weight
    if persona_id:
        payload["personaId"] = persona_id

    api_key = _load_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(GENERATE_URL, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call Suno generate endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"generate returned HTTP {response.status_code}: {response.text}",
            status_code=response.status_code,
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("generate endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("msg") or payload_json.get("message")
        raise RuntimeError(f"generate endpoint returned error code {payload_json.get('code')}: {message}")

    task_id = (payload_json.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError("generate endpoint did not return a taskId.")

    if log:
        _log(log, f"Suno task created: {task_id} (model={model})")

    return task_id, json.dumps(payload_json)
