"""Seedance 2.0 video helpers."""

import json
import time
from typing import Any

import torch

from .audio import _coerce_audio_to_wav_bytes
from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_audio, _upload_image, _upload_video
from .validation import _validate_image_tensor_batch, _validate_prompt
from .video import _coerce_video_to_mp4_bytes, _download_video, _video_bytes_to_comfy_video


MODEL_OPTIONS = ["bytedance/seedance-2-fast", "bytedance/seedance-2"]
DEFAULT_MODEL = "bytedance/seedance-2-fast"
PROMPT_MAX_LENGTH = 5000
ASPECT_RATIO_OPTIONS = ["16:9", "9:16", "1:1"]
RESOLUTION_OPTIONS = ["480p", "720p", "1080p"]
DURATION_OPTIONS = ["5", "10", "15"]


def _validation_error(message: str) -> RuntimeError:
    return RuntimeError(f"Seedance 2.0 validation error: {message}")


def _validate_frame_image(images: torch.Tensor | None, label: str) -> torch.Tensor:
    batch = _validate_image_tensor_batch(images)
    if batch.shape[0] > 1:
        raise _validation_error(f"{label} accepts a single image. Connect one image or slice the batch first.")
    return batch


def _validate_options(
    *,
    model: str,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    generate_audio: bool,
    return_last_frame: bool,
    web_search: bool,
) -> None:
    if model not in MODEL_OPTIONS:
        raise _validation_error("Invalid model. Use the pinned enum options.")
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise _validation_error("Invalid aspect_ratio. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise _validation_error("Invalid resolution. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise _validation_error("Invalid duration. Use the pinned enum options.")
    if not isinstance(generate_audio, bool):
        raise _validation_error("generate_audio must be a boolean value.")
    if not isinstance(return_last_frame, bool):
        raise _validation_error("return_last_frame must be a boolean value.")
    if not isinstance(web_search, bool):
        raise _validation_error("web_search must be a boolean value.")


def _detect_scenario(
    *,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    reference_images: torch.Tensor | None,
    reference_video: Any | None,
    reference_audio: Any | None,
) -> str:
    has_first = first_frame is not None
    has_last = last_frame is not None
    has_references = any(item is not None for item in (reference_images, reference_video, reference_audio))

    if has_last and not has_first:
        raise _validation_error("last_frame requires first_frame.")

    if has_first and has_last and has_references:
        return "first_last_frame_with_references"
    if has_first and has_references:
        return "first_frame_with_references"
    if has_first and has_last:
        return "first_last_frame"
    if has_first:
        return "first_frame"
    if has_references:
        return "multimodal_reference"
    return "text_to_video"


def _upload_single_frame(api_key: str, images: torch.Tensor | None, label: str, log: bool) -> str | None:
    if images is None:
        return None

    batch = _validate_frame_image(images, label)
    _log(log, f"Uploading {label} for Seedance 2.0...")
    image_url = _upload_image(api_key, _image_tensor_to_png_bytes(batch[0]))
    _log(log, f"{label} upload success: {_truncate_url(image_url)}")
    return image_url


def _upload_reference_images(api_key: str, images: torch.Tensor | None, log: bool) -> list[str]:
    if images is None:
        return []

    batch = _validate_image_tensor_batch(images)
    image_urls: list[str] = []
    _log(log, f"Uploading {batch.shape[0]} reference image(s) for Seedance 2.0...")
    for idx in range(batch.shape[0]):
        image_url = _upload_image(api_key, _image_tensor_to_png_bytes(batch[idx]))
        image_urls.append(image_url)
        _log(log, f"Reference image {idx + 1} upload success: {_truncate_url(image_url)}")
    return image_urls


def _upload_reference_video(api_key: str, reference_video: Any | None, log: bool) -> list[str]:
    if reference_video is None:
        return []

    video_bytes, source = _coerce_video_to_mp4_bytes(reference_video)
    _log(log, f"Uploading reference video for Seedance 2.0 ({source})...")
    video_url = _upload_video(api_key, video_bytes, filename="seedance2_reference.mp4")
    _log(log, f"Reference video upload success: {_truncate_url(video_url)}")
    return [video_url]


def _upload_reference_audio(api_key: str, reference_audio: Any | None, log: bool) -> list[str]:
    if reference_audio is None:
        return []

    audio_bytes, source = _coerce_audio_to_wav_bytes(reference_audio)
    _log(log, f"Uploading reference audio for Seedance 2.0 ({source})...")
    audio_url = _upload_audio(api_key, audio_bytes, filename="seedance2_reference.wav")
    _log(log, f"Reference audio upload success: {_truncate_url(audio_url)}")
    return [audio_url]


def _build_seedance2_payload(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    generate_audio: bool,
    return_last_frame: bool,
    web_search: bool,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    reference_images: torch.Tensor | None,
    reference_video: Any | None,
    reference_audio: Any | None,
    log: bool,
) -> tuple[dict[str, Any], str]:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(
        model=model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration=duration,
        generate_audio=generate_audio,
        return_last_frame=return_last_frame,
        web_search=web_search,
    )

    scenario = _detect_scenario(
        first_frame=first_frame,
        last_frame=last_frame,
        reference_images=reference_images,
        reference_video=reference_video,
        reference_audio=reference_audio,
    )
    api_key = _load_api_key()

    input_payload: dict[str, Any] = {
        "prompt": prompt,
        "return_last_frame": return_last_frame,
        "generate_audio": generate_audio,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "duration": int(duration),
        "web_search": web_search,
    }

    if scenario in {
        "first_frame",
        "first_last_frame",
        "first_frame_with_references",
        "first_last_frame_with_references",
    }:
        first_frame_url = _upload_single_frame(api_key, first_frame, "first_frame", log)
        if first_frame_url:
            input_payload["first_frame_url"] = first_frame_url

    if scenario in {"first_last_frame", "first_last_frame_with_references"}:
        last_frame_url = _upload_single_frame(api_key, last_frame, "last_frame", log)
        if last_frame_url:
            input_payload["last_frame_url"] = last_frame_url

    if scenario in {
        "multimodal_reference",
        "first_frame_with_references",
        "first_last_frame_with_references",
    }:
        reference_image_urls = _upload_reference_images(api_key, reference_images, log)
        reference_video_urls = _upload_reference_video(api_key, reference_video, log)
        reference_audio_urls = _upload_reference_audio(api_key, reference_audio, log)

        if reference_image_urls:
            input_payload["reference_image_urls"] = reference_image_urls
        if reference_video_urls:
            input_payload["reference_video_urls"] = reference_video_urls
        if reference_audio_urls:
            input_payload["reference_audio_urls"] = reference_audio_urls

    return {"model": model, "input": input_payload}, scenario


def summarize_seedance2_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_request_payload(payload)
    payload_input = normalized.get("input", {})

    reference_image_urls = list(payload_input.get("reference_image_urls") or [])
    reference_video_urls = list(payload_input.get("reference_video_urls") or [])
    reference_audio_urls = list(payload_input.get("reference_audio_urls") or [])

    fields_present = ["prompt", "return_last_frame", "generate_audio", "resolution", "aspect_ratio", "duration", "web_search"]
    for field_name in (
        "first_frame_url",
        "last_frame_url",
        "reference_image_urls",
        "reference_video_urls",
        "reference_audio_urls",
    ):
        if field_name in payload_input:
            fields_present.append(field_name)

    scenario = "text-to-video"
    if payload_input.get("first_frame_url") and payload_input.get("last_frame_url") and (
        reference_image_urls or reference_video_urls or reference_audio_urls
    ):
        scenario = "first+last-frame with references"
    elif payload_input.get("first_frame_url") and (
        reference_image_urls or reference_video_urls or reference_audio_urls
    ):
        scenario = "first-frame with references"
    elif payload_input.get("first_frame_url") and payload_input.get("last_frame_url"):
        scenario = "first+last-frame image-to-video"
    elif payload_input.get("first_frame_url"):
        scenario = "first-frame image-to-video"
    elif reference_image_urls or reference_video_urls or reference_audio_urls:
        scenario = "multimodal reference-to-video"

    return {
        "scenario": scenario,
        "model": normalized.get("model"),
        "fields_present": fields_present,
        "has_first_frame": bool(payload_input.get("first_frame_url")),
        "has_last_frame": bool(payload_input.get("last_frame_url")),
        "reference_image_count": len(reference_image_urls),
        "reference_video_count": len(reference_video_urls),
        "reference_audio_count": len(reference_audio_urls),
        "reference_image_aliases": [f"@Image{idx}" for idx in range(1, len(reference_image_urls) + 1)],
        "reference_video_aliases": [f"@Video{idx}" for idx in range(1, len(reference_video_urls) + 1)],
        "reference_audio_aliases": [f"@Audio{idx}" for idx in range(1, len(reference_audio_urls) + 1)],
    }


def preflight_seedance2_payload(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    generate_audio: bool,
    return_last_frame: bool,
    web_search: bool,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    reference_images: torch.Tensor | None,
    reference_video: Any | None,
    reference_audio: Any | None,
    log: bool,
) -> dict[str, Any]:
    payload, _scenario = _build_seedance2_payload(
        model=model,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration=duration,
        generate_audio=generate_audio,
        return_last_frame=return_last_frame,
        web_search=web_search,
        first_frame=first_frame,
        last_frame=last_frame,
        reference_images=reference_images,
        reference_video=reference_video,
        reference_audio=reference_audio,
        log=log,
    )
    return payload


def run_seedance2_video_payload(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    generate_audio: bool,
    return_last_frame: bool,
    web_search: bool,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    reference_images: torch.Tensor | None,
    reference_video: Any | None,
    reference_audio: Any | None,
    log: bool,
) -> tuple[dict[str, Any], str]:
    return _build_seedance2_payload(
        model=model,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration=duration,
        generate_audio=generate_audio,
        return_last_frame=return_last_frame,
        web_search=web_search,
        first_frame=first_frame,
        last_frame=last_frame,
        reference_images=reference_images,
        reference_video=reference_video,
        reference_audio=reference_audio,
        log=log,
    )


def _normalize_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if normalized.get("model") not in MODEL_OPTIONS:
        raise _validation_error("request payload model must be one of the supported Seedance 2.0 models.")

    payload_input = normalized.get("input")
    if not isinstance(payload_input, dict):
        raise _validation_error("request payload must include an input object.")

    normalized_input = dict(payload_input)
    if "reference_video_urls " in normalized_input and "reference_video_urls" not in normalized_input:
        normalized_input["reference_video_urls"] = normalized_input.pop("reference_video_urls ")

    normalized["input"] = normalized_input
    return normalized


def _select_video_url(result_urls: list[str]) -> str:
    for url in result_urls:
        lower = str(url).lower()
        if any(lower.endswith(ext) for ext in (".mp4", ".mov", ".webm", ".m4v")):
            return url
    return result_urls[0]


def run_seedance2_video(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    generate_audio: bool,
    return_last_frame: bool,
    web_search: bool,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    reference_images: torch.Tensor | None,
    reference_video: Any | None,
    reference_audio: Any | None,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    payload, _scenario = run_seedance2_video_payload(
        model=model,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration=duration,
        generate_audio=generate_audio,
        return_last_frame=return_last_frame,
        web_search=web_search,
        first_frame=first_frame,
        last_frame=last_frame,
        reference_images=reference_images,
        reference_video=reference_video,
        reference_audio=reference_audio,
        log=log,
    )
    return run_seedance2_video_from_request(
        payload=payload,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_seedance2_video_from_request(
    *,
    payload: dict[str, Any],
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    if not isinstance(payload, dict):
        raise _validation_error("request payload must be an object.")

    payload = _normalize_request_payload(payload)

    _log(log, "Creating Seedance 2.0 task...")
    start_time = time.time()
    api_key = _load_api_key()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    result_urls = _extract_result_urls(record_data)
    video_url = _select_video_url(result_urls)
    if len(result_urls) > 1:
        _log(log, f"Seedance 2.0 returned {len(result_urls)} result URLs; selecting video URL {video_url}")
    else:
        _log(log, f"Final video URL: {video_url}")

    video_bytes = _download_video(video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output
