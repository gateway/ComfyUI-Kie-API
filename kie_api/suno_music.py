"""KIE Suno music generation helper (v1 create-only)."""

import json
import time
from typing import Any

import torch
from .auth import _load_api_key
from .audio import _audio_bytes_to_comfy_audio
from .images import _download_image, _image_bytes_to_tensor
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


def _format_record_for_output(record: dict[str, Any]) -> str:
    try:
        record_copy = json.loads(json.dumps(record))
    except TypeError:
        record_copy = dict(record)

    param_value = record_copy.get("param")
    if isinstance(param_value, str):
        try:
            record_copy["param"] = json.loads(param_value)
        except json.JSONDecodeError:
            record_copy["param"] = param_value

    return json.dumps(record_copy, indent=2, ensure_ascii=False, default=str)


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


def _extract_image_urls(record_data: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    # Callback-style payload: data.data[].image_url
    items = record_data.get("data")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                image_url = item.get("image_url") or item.get("imageUrl")
                if image_url:
                    urls.append(image_url)

    # record-info payload: data.response.sunoData[].imageUrl
    response = record_data.get("response")
    if isinstance(response, dict):
        suno_data = response.get("sunoData")
        if isinstance(suno_data, list):
            for item in suno_data:
                if isinstance(item, dict):
                    image_url = item.get("imageUrl") or item.get("image_url")
                    if image_url:
                        urls.append(image_url)

    # direct field fallback
    if not urls and isinstance(record_data, dict):
        image_url = record_data.get("image_url") or record_data.get("imageUrl")
        if image_url:
            urls.append(image_url)

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
) -> tuple[dict, dict, str, torch.Tensor, torch.Tensor]:
    """Create a Suno music generation task and return two audio outputs + formatted record-info JSON + two cover images."""
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
    if len(audio_urls) < 2:
        raise RuntimeError("Expected two audio_url entries in record-info response.")
    audio_url_1 = audio_urls[0]
    audio_url_2 = audio_urls[1]
    if log:
        _log(log, f"Suno audio URL 1: {audio_url_1}")
        _log(log, f"Suno audio URL 2: {audio_url_2}")

    try:
        response_1 = requests.get(audio_url_1, timeout=180)
        response_2 = requests.get(audio_url_2, timeout=180)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download audio: {exc}") from exc
    if response_1.status_code != 200:
        raise RuntimeError(f"Failed to download audio 1 (status code {response_1.status_code}).")
    if response_2.status_code != 200:
        raise RuntimeError(f"Failed to download audio 2 (status code {response_2.status_code}).")

    audio_bytes_1 = response_1.content
    audio_bytes_2 = response_2.content

    audio_output_1 = _audio_bytes_to_comfy_audio(audio_bytes_1, "audio_1.mp3")
    audio_output_2 = _audio_bytes_to_comfy_audio(audio_bytes_2, "audio_2.mp3")
    try:
        import torch
        for audio_output in (audio_output_1, audio_output_2):
            waveform = audio_output.get("waveform")
            if not isinstance(waveform, torch.Tensor):
                waveform = torch.as_tensor(waveform)
            if waveform.ndim == 1:
                waveform = waveform.unsqueeze(0)
            if waveform.ndim == 2:
                waveform = waveform.unsqueeze(0)
            audio_output["waveform"] = waveform
    except Exception as exc:
        raise RuntimeError(f"Failed to normalize audio waveform for ComfyUI: {exc}") from exc
    if log:
        waveform_1 = audio_output_1.get("waveform")
        shape_1 = getattr(waveform_1, "shape", None)
        _log(log, f"Suno audio 1 waveform shape: {shape_1}")
        waveform_2 = audio_output_2.get("waveform")
        shape_2 = getattr(waveform_2, "shape", None)
        _log(log, f"Suno audio 2 waveform shape: {shape_2}")

    image_urls = _extract_image_urls(record)
    if len(image_urls) < 2:
        raise RuntimeError("Expected two image_url entries in record-info response.")
    image_url_1 = image_urls[0]
    image_url_2 = image_urls[1]
    if log:
        _log(log, f"Suno cover image URL 1: {image_url_1}")
        _log(log, f"Suno cover image URL 2: {image_url_2}")
    try:
        image_bytes_1 = _download_image(image_url_1)
        image_tensor_1 = _image_bytes_to_tensor(image_bytes_1)
        image_bytes_2 = _download_image(image_url_2)
        image_tensor_2 = _image_bytes_to_tensor(image_bytes_2)
    except Exception as exc:
        raise RuntimeError(f"Failed to download cover image: {exc}") from exc

    return audio_output_1, audio_output_2, _format_record_for_output(record), image_tensor_1, image_tensor_2
