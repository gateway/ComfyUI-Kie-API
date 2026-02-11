"""Kling 3.0 video helpers and element preparation."""

import re
import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image, _upload_video
from .validation import _validate_prompt
from .video import _coerce_video_to_mp4_bytes, _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "kling-3.0/video"
MODE_OPTIONS = ["std", "pro"]
ASPECT_RATIO_OPTIONS = ["1:1", "9:16", "16:9"]
DURATION_OPTIONS = [str(i) for i in range(3, 16)]
MULTI_SHOT_MIN = 1
MULTI_SHOT_MAX = 12
PROMPT_MAX_LENGTH = 2500
ELEMENT_IMAGE_MIN = 2
ELEMENT_IMAGE_MAX = 4
ELEMENT_BATCH_MAX = 9


def _validation_error(message: str) -> RuntimeError:
    return RuntimeError(f"Kling 3.0 validation error: {message}")


def _validate_batch_image(images: torch.Tensor | None, label: str) -> torch.Tensor:
    if images is None:
        raise _validation_error(f"{label} input is required.")
    if not isinstance(images, torch.Tensor):
        raise _validation_error(f"{label} input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise _validation_error(f"{label} input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise _validation_error(f"{label} input batch is empty.")
    return images


def _extract_referenced_elements(text: str) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"@([a-zA-Z0-9_\\-]+)", text))


def _parse_multi_prompt_text(shots_text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in (shots_text or "").splitlines() if line.strip()]
    if not lines:
        raise _validation_error("multi_shots is enabled but shots_text is empty.")

    shots: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == 2:
            duration_str, prompt = parts
        elif len(parts) >= 3:
            duration_str, prompt = parts[1], "|".join(parts[2:]).strip()
        else:
            raise _validation_error(
                f"Invalid shots_text format on line {idx}. "
                "Use 'duration | prompt' or 'label | duration | prompt'. "
                "Example: '3 | A dog runs through fog' or 'shot1 | 3 | A dog runs through fog'."
            )

        try:
            duration = int(duration_str)
        except ValueError as exc:
            raise _validation_error(f"Invalid shot duration '{duration_str}' on line {idx}.") from exc

        if duration < MULTI_SHOT_MIN or duration > MULTI_SHOT_MAX:
            raise _validation_error(
                f"Shot duration on line {idx} must be between {MULTI_SHOT_MIN} and {MULTI_SHOT_MAX} seconds."
            )

        _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
        shots.append({"prompt": prompt, "duration": duration})

    return shots


def build_kling3_element(
    *,
    name: str,
    description: str,
    images: torch.Tensor | None,
    video: Any | None,
    log: bool,
) -> dict[str, Any]:
    """Build one Kling element with uploaded URLs for image or video."""
    element_name = (name or "").strip()
    if not element_name:
        raise _validation_error("Element name is required.")
    if not re.match(r"^[a-zA-Z0-9_\\-]+$", element_name):
        raise _validation_error("Element name may only contain letters, numbers, underscore, or hyphen.")

    has_images = images is not None
    has_video = video is not None
    if has_images and has_video:
        raise _validation_error(
            "Element cannot contain both images and video. Connect one media type per element."
        )
    if not has_images and not has_video:
        raise _validation_error("Element requires either images or video.")

    api_key = _load_api_key()
    description_text = (description or "").strip()

    if has_images:
        image_batch = _validate_batch_image(images, "images")
        image_count = image_batch.shape[0]
        if image_count < ELEMENT_IMAGE_MIN or image_count > ELEMENT_IMAGE_MAX:
            raise _validation_error(
                f"Element images must contain {ELEMENT_IMAGE_MIN}-{ELEMENT_IMAGE_MAX} images; got {image_count}."
            )

        image_urls: list[str] = []
        _log(log, f"Uploading {image_count} element image(s) for '{element_name}'...")
        for idx in range(image_count):
            png_bytes = _image_tensor_to_png_bytes(image_batch[idx])
            image_url = _upload_image(api_key, png_bytes)
            image_urls.append(image_url)
            _log(log, f"Element image {idx + 1} upload success: {_truncate_url(image_url)}")

        payload: dict[str, Any] = {
            "name": element_name,
            "description": description_text,
            "element_input_urls": image_urls,
        }
        return payload

    video_bytes, source = _coerce_video_to_mp4_bytes(video)
    _log(log, f"Uploading element video for '{element_name}' ({source})...")
    video_url = _upload_video(api_key, video_bytes, filename=f"{element_name}.mp4")
    _log(log, f"Element video upload success: {_truncate_url(video_url)}")
    return {
        "name": element_name,
        "description": description_text,
        "element_input_video_urls": [video_url],
    }


def merge_kling3_elements(*elements: Any) -> list[dict[str, Any]]:
    """Merge up to the supported max element payloads."""
    merged: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for item in elements:
        if item is None:
            continue
        if not isinstance(item, dict):
            raise _validation_error("Element batch inputs must be KIE_ELEMENT payload objects.")

        name = str(item.get("name") or "").strip()
        if not name:
            raise _validation_error("Element payload missing name.")
        if name in seen_names:
            raise _validation_error(f"Duplicate element name '{name}' in elements batch.")
        seen_names.add(name)
        merged.append(item)

    if len(merged) > ELEMENT_BATCH_MAX:
        raise _validation_error(f"Element batch supports up to {ELEMENT_BATCH_MAX} elements.")
    return merged


def _build_kling3_payload(
    *,
    mode: str,
    aspect_ratio: str,
    duration: str,
    multi_shots: bool,
    sound: bool,
    prompt: str,
    shots_text: str,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    elements: list[dict[str, Any]] | None,
    log: bool,
) -> tuple[dict[str, Any], str]:
    """Build Kling 3.0 createTask payload after validation/uploads.

    Returns:
        (payload, resolved_duration)
    """
    if mode not in MODE_OPTIONS:
        raise _validation_error("Invalid mode. Use one of: std, pro.")
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise _validation_error("Invalid aspect_ratio. Use one of: 1:1, 9:16, 16:9.")
    if duration not in DURATION_OPTIONS:
        raise _validation_error("Invalid duration. Use 3-15 seconds.")

    if multi_shots and sound:
        raise _validation_error("sound=true is not allowed when multi_shots=true. Set sound=false.")

    api_key = _load_api_key()
    frame_urls: list[str] = []

    if first_frame is not None:
        first_batch = _validate_batch_image(first_frame, "first_frame")
        if first_batch.shape[0] > 1:
            _log(log, f"More than 1 first_frame image provided ({first_batch.shape[0]}); using the first.")
        _log(log, "Uploading first frame...")
        first_url = _upload_image(api_key, _image_tensor_to_png_bytes(first_batch[0]))
        frame_urls.append(first_url)
        _log(log, f"First frame upload success: {_truncate_url(first_url)}")

    if last_frame is not None:
        if multi_shots:
            raise _validation_error("last_frame is not allowed when multi_shots=true.")
        last_batch = _validate_batch_image(last_frame, "last_frame")
        if last_batch.shape[0] > 1:
            _log(log, f"More than 1 last_frame image provided ({last_batch.shape[0]}); using the first.")
        _log(log, "Uploading last frame...")
        last_url = _upload_image(api_key, _image_tensor_to_png_bytes(last_batch[0]))
        frame_urls.append(last_url)
        _log(log, f"Last frame upload success: {_truncate_url(last_url)}")

    payload_input: dict[str, Any] = {
        "mode": mode,
        "multi_shots": multi_shots,
    }
    resolved_duration = duration
    if not multi_shots:
        _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
        payload_input["prompt"] = prompt
        payload_input["sound"] = bool(sound)
    else:
        multi_prompt = _parse_multi_prompt_text(shots_text)
        total_duration = sum(int(item["duration"]) for item in multi_prompt)
        if total_duration < 3 or total_duration > 15:
            raise _validation_error("Total multi-shot duration must be between 3 and 15 seconds.")
        if int(duration) != total_duration:
            _log(
                log,
                f"multi_shots enabled: overriding duration={duration} with computed total={total_duration}.",
            )
        resolved_duration = str(total_duration)
        payload_input["multi_prompt"] = multi_prompt
    payload_input["duration"] = resolved_duration

    if frame_urls:
        payload_input["image_urls"] = frame_urls

    # aspect_ratio must be omitted when both start/end frames are used.
    if len(frame_urls) < 2:
        payload_input["aspect_ratio"] = aspect_ratio

    referenced = _extract_referenced_elements(prompt)
    if multi_shots:
        for shot in payload_input.get("multi_prompt", []):
            referenced |= _extract_referenced_elements(str(shot.get("prompt") or ""))

    if referenced and not frame_urls:
        raise _validation_error(
            "Prompt uses @element references but no first_frame/image_urls were provided. "
            "Connect first_frame when using elements."
        )

    if elements:
        if len(elements) > ELEMENT_BATCH_MAX:
            raise _validation_error(f"At most {ELEMENT_BATCH_MAX} elements are supported in this node.")
        payload_input["kling_elements"] = elements

        available = {str(item.get("name") or "").strip() for item in elements}
        missing = sorted(ref for ref in referenced if ref not in available)
        if missing:
            raise _validation_error(
                "Prompt references unknown @elements: " + ", ".join(f"@{name}" for name in missing)
            )
    elif referenced:
        raise _validation_error(
            "Prompt contains @element references but no elements were provided. "
            "Add KIE Kling Elements + KIE Kling Elements Batch inputs."
        )

    payload = {"model": MODEL_NAME, "input": payload_input}
    return payload, resolved_duration


def preflight_kling3_payload(
    *,
    mode: str,
    aspect_ratio: str,
    duration: str,
    multi_shots: bool,
    sound: bool,
    prompt: str,
    shots_text: str,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    elements: list[dict[str, Any]] | None,
    log: bool,
) -> dict[str, Any]:
    """Build and return createTask payload only (no task submission)."""
    payload, _resolved_duration = run_kling3_video_payload(
        mode=mode,
        aspect_ratio=aspect_ratio,
        duration=duration,
        multi_shots=multi_shots,
        sound=sound,
        prompt=prompt,
        shots_text=shots_text,
        first_frame=first_frame,
        last_frame=last_frame,
        elements=elements,
        log=log,
    )
    return payload


def run_kling3_video_payload(
    *,
    mode: str,
    aspect_ratio: str,
    duration: str,
    multi_shots: bool,
    sound: bool,
    prompt: str,
    shots_text: str,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    elements: list[dict[str, Any]] | None,
    log: bool,
) -> tuple[dict[str, Any], str]:
    """Public payload builder used by preflight and generation."""
    return _build_kling3_payload(
        mode=mode,
        aspect_ratio=aspect_ratio,
        duration=duration,
        multi_shots=multi_shots,
        sound=sound,
        prompt=prompt,
        shots_text=shots_text,
        first_frame=first_frame,
        last_frame=last_frame,
        elements=elements,
        log=log,
    )


def run_kling3_video(
    *,
    mode: str,
    aspect_ratio: str,
    duration: str,
    multi_shots: bool,
    sound: bool,
    prompt: str,
    shots_text: str,
    first_frame: torch.Tensor | None,
    last_frame: torch.Tensor | None,
    elements: list[dict[str, Any]] | None,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    """Run Kling 3.0 video generation."""
    payload, _resolved_duration = run_kling3_video_payload(
        mode=mode,
        aspect_ratio=aspect_ratio,
        duration=duration,
        multi_shots=multi_shots,
        sound=sound,
        prompt=prompt,
        shots_text=shots_text,
        first_frame=first_frame,
        last_frame=last_frame,
        elements=elements,
        log=log,
    )
    return run_kling3_video_from_request(
        payload=payload,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_kling3_video_from_request(
    *,
    payload: dict[str, Any],
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    """Submit a prebuilt Kling 3.0 createTask payload and return VIDEO output."""
    if not isinstance(payload, dict):
        raise _validation_error("request payload must be an object.")
    if payload.get("model") != MODEL_NAME:
        raise _validation_error(f"request payload model must be '{MODEL_NAME}'.")
    payload_input = payload.get("input")
    if not isinstance(payload_input, dict):
        raise _validation_error("request payload must include an input object.")

    _log(log, "Creating Kling 3.0 video task...")
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
    video_url = result_urls[0]
    _log(log, f"Final video URL: {video_url}")

    video_bytes = _download_video(video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output
