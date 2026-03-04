"""Grok Imagine image-to-video helper."""

import time
from typing import Optional

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch, _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "grok-imagine/image-to-video"
PROMPT_MAX_LENGTH = 5000
MODE_OPTIONS = ["normal", "fun", "spicy"]
DURATION_OPTIONS = ["6", "10", "15"]
RESOLUTION_OPTIONS = ["480p", "720p"]


def run_grok_imagine_i2v_video(
    prompt: str,
    images: Optional[torch.Tensor],
    task_id_ref: str,
    index: int,
    mode: str,
    duration: str,
    resolution: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> dict:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    if mode not in MODE_OPTIONS:
        raise RuntimeError("Invalid mode. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")

    has_images = images is not None
    has_task_id = bool((task_id_ref or "").strip())

    if has_images and has_task_id:
        raise RuntimeError("Provide either 'images' or 'task_id', not both.")
    if not has_images and not has_task_id:
        raise RuntimeError(
            "Provide either 'images' (upload path) or 'task_id' (Grok-generated image reference)."
        )

    api_key = _load_api_key()

    input_payload: dict = {
        "prompt": prompt,
        "mode": mode,
        "duration": duration,
        "resolution": resolution,
    }

    if has_images:
        images = _validate_image_tensor_batch(images)
        if images.shape[0] > 1:
            _log(
                log,
                f"More than 1 image provided ({images.shape[0]}); only the first will be used.",
            )
        _log(log, "Uploading source image for Grok Imagine I2V...")
        png_bytes = _image_tensor_to_png_bytes(images[0])
        image_url = _upload_image(api_key, png_bytes)
        _log(log, f"Image upload success: {_truncate_url(image_url)}")
        input_payload["image_urls"] = [image_url]
    else:
        _log(log, f"Using Grok task_id reference: {task_id_ref.strip()} index={index}")
        input_payload["task_id"] = task_id_ref.strip()
        input_payload["index"] = index

    payload = {
        "model": MODEL_NAME,
        "input": input_payload,
    }

    _log(log, "Creating Grok Imagine I2V task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(
        log,
        f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}",
    )
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
