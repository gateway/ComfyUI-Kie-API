"""Kling 3.0 motion-control image-to-video helper."""

import hashlib
import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image, _upload_video
from .validation import _validate_image_tensor_batch
from .video import _coerce_video_to_mp4_bytes, _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "kling-3.0/motion-control"
PROMPT_MAX_LENGTH = 2500
CHARACTER_ORIENTATION_OPTIONS = ["image", "video"]
MODE_OPTIONS = ["720p", "1080p"]
MODE_ALIASES = {"std": "720p", "pro": "1080p"}
IMAGE_MIN_EDGE_PX = 301
IMAGE_MIN_ASPECT_RATIO = 2.0 / 5.0
IMAGE_MAX_ASPECT_RATIO = 5.0 / 2.0
VIDEO_MAX_SIZE_BYTES = 100 * 1024 * 1024


def _validate_optional_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise RuntimeError("prompt must be a string.")

    prompt_value = prompt.strip()
    if len(prompt_value) > PROMPT_MAX_LENGTH:
        raise RuntimeError(f"Prompt exceeds the maximum length of {PROMPT_MAX_LENGTH} characters.")

    return prompt_value


def _normalize_mode(mode: str) -> str:
    if not isinstance(mode, str):
        raise RuntimeError("mode must be a string.")

    normalized = MODE_ALIASES.get(mode, mode)
    if normalized not in MODE_OPTIONS:
        raise RuntimeError("Invalid mode. Use the pinned enum options.")
    return normalized


def _validate_character_orientation(character_orientation: str) -> str:
    if character_orientation not in CHARACTER_ORIENTATION_OPTIONS:
        raise RuntimeError("Invalid character_orientation. Use the pinned enum options.")
    return character_orientation


def _validate_reference_image_constraints(image: torch.Tensor) -> None:
    height = int(image.shape[0])
    width = int(image.shape[1])

    if height < IMAGE_MIN_EDGE_PX or width < IMAGE_MIN_EDGE_PX:
        raise RuntimeError("Reference image width and height must both be greater than 300px.")

    aspect_ratio = width / height if height else 0.0
    if aspect_ratio < IMAGE_MIN_ASPECT_RATIO or aspect_ratio > IMAGE_MAX_ASPECT_RATIO:
        raise RuntimeError("Reference image aspect ratio must stay between 2:5 and 5:2.")


def _validate_video_input(video: Any) -> Any:
    if video is None:
        raise RuntimeError("video input is required.")
    return video


def _validate_video_bytes(video_bytes: bytes) -> None:
    if len(video_bytes) > VIDEO_MAX_SIZE_BYTES:
        raise RuntimeError("Reference video exceeds the 100MB maximum size.")


def _build_motion_upload_filename(video_bytes: bytes) -> tuple[str, str]:
    fingerprint = hashlib.sha1(video_bytes).hexdigest()[:12]
    filename = f"motion_{int(time.time() * 1000)}_{fingerprint}.mp4"
    return filename, fingerprint


def run_kling3motion_i2v_video(
    prompt: str,
    images: torch.Tensor,
    video: Any,
    character_orientation: str = "video",
    mode: str = "720p",
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> Any:
    prompt_value = _validate_optional_prompt(prompt)
    character_orientation = _validate_character_orientation(character_orientation)
    mode_value = _normalize_mode(mode)
    images = _validate_image_tensor_batch(images)
    video = _validate_video_input(video)

    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    _validate_reference_image_constraints(images[0])

    _log(log, "Uploading reference image for Kling 3.0 Motion I2V...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    video_bytes, source_desc = _coerce_video_to_mp4_bytes(video)
    _validate_video_bytes(video_bytes)
    upload_filename, video_fingerprint = _build_motion_upload_filename(video_bytes)
    _log(log, f"Motion video source: {source_desc}")
    _log(log, f"Motion video fingerprint: {video_fingerprint}")

    _log(log, "Uploading motion reference video for Kling 3.0 Motion I2V...")
    video_url = _upload_video(api_key, video_bytes, filename=upload_filename)
    _log(log, f"Video upload success: {_truncate_url(video_url)}")

    input_payload = {
        "input_urls": [image_url],
        "video_urls": [video_url],
        "character_orientation": character_orientation,
        # KIE docs conflict on std/pro vs 720p/1080p; pin to the explicit example/options table.
        "mode": mode_value,
    }
    if prompt_value:
        input_payload["prompt"] = prompt_value

    payload = {
        "model": MODEL_NAME,
        "input": input_payload,
    }

    _log(log, "Creating Kling 3.0 Motion I2V task...")
    start_time = time.time()
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
    result_video_url = result_urls[0]
    _log(log, f"Final video URL: {result_video_url}")

    result_video_bytes = _download_video(result_video_url)
    video_output = _video_bytes_to_comfy_video(result_video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output


def run_kling3motion_i2v(
    prompt: str,
    images: torch.Tensor,
    video: Any,
    character_orientation: str = "video",
    mode: str = "720p",
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> Any:
    """Backward-compatible alias for existing imports."""
    return run_kling3motion_i2v_video(
        prompt=prompt,
        images=images,
        video=video,
        character_orientation=character_orientation,
        mode=mode,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
