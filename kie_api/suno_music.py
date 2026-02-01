"""KIE Suno music generation helper (v1 create-only)."""

import json
import time
from typing import Any

from .auth import _load_api_key
from .audio import _audio_bytes_to_comfy_audio
from .http import TransientKieError, requests
from .log import _log

GENERATE_URL = "https://api.kie.ai/api/v1/generate"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/generate/record-info"
MODEL_OPTIONS = ["V4", "V4_5", "V4_5PLUS", "V4_5ALL", "V5"]
VOCAL_GENDER_OPTIONS = ["m", "f"]
POLLABLE_STATES = {"PENDING", "TEXT_SUCCESS", "FIRST_SUCCESS"}
SUCCESS_STATE = "SUCCESS"
FAIL_STATES = {
    "CREATE_TASK_FAILED",
    "GENERATE_AUDIO_FAILED",
    "CALLBACK_EXCEPTION",
    "SENSITIVE_WORD_ERROR",
}


def _validate_length(field_name: str, value: str | None, max_len: int) -> None:
    if value is None:
        return
    if len(value) > max_len:
        raise RuntimeError(f"{field_name} exceeds max length of {max_len} characters.")


def _max_prompt_len(model: str) -> int:
    return 3000 if model == "V4" else 5000


def _max_style_len(model: str) -> int:
    return 200 if model == "V4" else 1000


def _fetch_music_record(api_key: str, task_id: str) -> dict[str, Any]:
    try:
        response = requests.get(
            RECORD_INFO_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"taskId": task_id},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call record-info endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"record-info returned HTTP {response.status_code}: {response.text}",
            status_code=response.status_code,
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("record-info endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("msg") or payload_json.get("message")
        raise RuntimeError(f"record-info returned error code {payload_json.get('code')}: {message}")

    data = payload_json.get("data")
    if data is None:
        raise RuntimeError("record-info endpoint returned no data field.")

    return data


def _extract_audio_urls(record_data: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    # Callback-style payload: data.data[].audio_url
    items = record_data.get("data")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                audio_url = item.get("audio_url") or item.get("audioUrl")
                stream_url = item.get("stream_audio_url") or item.get("streamAudioUrl")
                if audio_url:
                    urls.append(audio_url)
                elif stream_url:
                    urls.append(stream_url)

    # record-info payload: data.response.sunoData[].audioUrl
    response = record_data.get("response")
    if isinstance(response, dict):
        suno_data = response.get("sunoData")
        if isinstance(suno_data, list):
            for item in suno_data:
                if isinstance(item, dict):
                    audio_url = item.get("audioUrl") or item.get("audio_url")
                    stream_url = item.get("streamAudioUrl") or item.get("stream_audio_url")
                    if audio_url:
                        urls.append(audio_url)
                    elif stream_url:
                        urls.append(stream_url)

    # direct field fallback
    if not urls and isinstance(record_data, dict):
        audio_url = record_data.get("audio_url") or record_data.get("audioUrl")
        if audio_url:
            urls.append(audio_url)

    if not urls:
        raise RuntimeError("No audio_url found in record-info response.")
    return urls


def _poll_music_until_complete(
    api_key: str,
    task_id: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> dict[str, Any]:
    start_time = time.time()
    last_state = None

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_s:
            raise RuntimeError(f"Task {task_id} timed out after {timeout_s}s.")

        record = _fetch_music_record(api_key, task_id)
        state = record.get("status") or record.get("state") or record.get("callbackType")

        if log and state != last_state:
            _log(log, f"Suno task {task_id} state: {state}")
            last_state = state

        if state == SUCCESS_STATE or state == "complete":
            return record
        if state in FAIL_STATES or state == "error":
            raise RuntimeError(f"Suno task {task_id} failed with state: {state}")

        if state in POLLABLE_STATES or state is None:
            time.sleep(poll_interval_s)
            continue

        # Unknown state, keep polling conservatively
        time.sleep(poll_interval_s)


def run_suno_generate(
    *,
    prompt: str,
    custom_mode: bool,
    instrumental: bool,
    model: str,
    style: str | None = None,
    title: str | None = None,
    negative_tags: str | None = None,
    vocal_gender: str | None = None,
    style_weight: float | None = None,
    weirdness_constraint: float | None = None,
    audio_weight: float | None = None,
    poll_interval_s: float = 30.0,
    timeout_s: int = 1800,
    log: bool = True,
) -> tuple[dict, str, str]:
    """Create a Suno music generation task and return audio output."""
    if model not in MODEL_OPTIONS:
        raise RuntimeError("Invalid model. Use the pinned enum options.")
    if vocal_gender and vocal_gender not in VOCAL_GENDER_OPTIONS:
        raise RuntimeError("vocal_gender must be 'm' or 'f'.")
    callback_url = "https://example.com/kie-suno-callback"

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
        if any([style_text, title_text, negative_tags, vocal_gender]):
            raise RuntimeError("style/title/negative_tags/vocal_gender must be empty when custom_mode is false.")

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

    record = _poll_music_until_complete(
        api_key,
        task_id,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
    if log:
        _log(log, f"Suno record-info response keys: {list(record.keys())}")
    audio_urls = _extract_audio_urls(record)
    audio_url = audio_urls[0]
    if log:
        _log(log, f"Suno audio URL: {audio_url}")

    try:
        audio_bytes = requests.get(audio_url, timeout=180).content
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download audio: {exc}") from exc

    audio_output = _audio_bytes_to_comfy_audio(audio_bytes, "audio.mp3")
    return audio_output, task_id, json.dumps(payload_json)
