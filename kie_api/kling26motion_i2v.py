"""Kling 2.6 motion-control image-to-video helper."""

import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image, _upload_video
from .validation import _validate_image_tensor_batch, _validate_prompt
from .video import _coerce_video_to_mp4_bytes, _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "kling-2.6/motion-control"
PROMPT_MAX_LENGTH = 2500
CHARACTER_ORIENTATION_OPTIONS = ["image", "video"]
MODE_OPTIONS = ["720p", "1080p"]


def _validate_options(character_orientation: str, mode: str) -> None:
    if character_orientation not in CHARACTER_ORIENTATION_OPTIONS:
        raise RuntimeError("Invalid character_orientation. Use the pinned enum options.")
    if mode not in MODE_OPTIONS:
        raise RuntimeError("Invalid mode. Use the pinned enum options.")


def _validate_video_input(video: Any) -> Any:
    if video is None:
        raise RuntimeError("video input is required.")
    return video


def run_kling26motion_i2v_video(
    prompt: str,
    images: torch.Tensor,
    video: Any,
    character_orientation: str = "video",
    mode: str = "720p",
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> Any:
    # Validate prompt length and required inputs.
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(character_orientation, mode)
    images = _validate_image_tensor_batch(images)
    video = _validate_video_input(video)

    # Load the API key once for uploads and task creation.
    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    # Upload the reference image using the shared upload helper.
    _log(log, "Uploading reference image for Kling 2.6 Motion I2V...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    # Resolve the input video into MP4 bytes so it can be uploaded.
    video_bytes, source_desc = _coerce_video_to_mp4_bytes(video)
    _log(log, f"Motion video source: {source_desc}")

    # Upload the motion reference video using the shared upload helper.
    _log(log, "Uploading motion reference video for Kling 2.6 Motion I2V...")
    video_url = _upload_video(api_key, video_bytes, filename="motion.mp4")
    _log(log, f"Video upload success: {_truncate_url(video_url)}")

    # Build the createTask payload exactly as required by the KIE API spec.
    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "input_urls": [image_url],
            "video_urls": [video_url],
            "character_orientation": character_orientation,
            "mode": mode,
        },
    }

    # Create the task and log the raw response for troubleshooting.
    _log(log, "Creating Kling 2.6 Motion I2V task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    # Poll until the job finishes or times out.
    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    # Extract the final video URL from the result payload.
    result_urls = _extract_result_urls(record_data)
    result_video_url = result_urls[0]
    _log(log, f"Final video URL: {result_video_url}")

    # Download the video bytes and return a VIDEO-compatible object.
    result_video_bytes = _download_video(result_video_url)
    video_output = _video_bytes_to_comfy_video(result_video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output


def run_kling26motion_i2v(
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
    return run_kling26motion_i2v_video(
        prompt=prompt,
        images=images,
        video=video,
        character_orientation=character_orientation,
        mode=mode,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
