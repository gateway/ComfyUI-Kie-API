"""Kling 2.5 Turbo Image-to-Video Pro helper."""

import time
from typing import Any, Callable

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "kling/v2-5-turbo-image-to-video-pro"
PROMPT_MAX_LENGTH = 1000
DURATION_OPTIONS = ["5", "10"]


def _validate_options(duration: str, cfg_scale: float) -> None:
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if not isinstance(cfg_scale, (int, float)):
        raise RuntimeError("cfg_scale must be a float value.")
    if cfg_scale < 0.0 or cfg_scale > 1.0:
        raise RuntimeError("cfg_scale must be between 0.0 and 1.0.")


def _validate_image_input(images: torch.Tensor | None, *, label: str, required: bool) -> torch.Tensor | None:
    if images is None:
        if required:
            raise RuntimeError(f"{label} input is required.")
        return None
    if not isinstance(images, torch.Tensor):
        raise RuntimeError(f"{label} input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise RuntimeError(f"{label} input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise RuntimeError(f"{label} input batch is empty.")
    return images


def run_kling25_i2v_job(
    image: torch.Tensor,
    tail_image: torch.Tensor | None,
    prompt: str,
    negative_prompt: str = "",
    duration: str = "5",
    cfg_scale: float = 0.5,
    timeout_seconds: int | None = None,
    log: Callable[[str], None] | None = None,
) -> dict:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(duration, cfg_scale)
    images = _validate_image_input(image, label="image", required=True)
    tail_images = _validate_image_input(tail_image, label="tail_image", required=False)

    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")
    if tail_images is not None and tail_images.shape[0] > 1:
        _log(log, f"More than 1 tail image provided ({tail_images.shape[0]}); only the first will be used.")

    _log(log, "Uploading source image for Kling 2.5 I2V Pro...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    tail_image_url = None
    if tail_images is not None:
        _log(log, "Uploading tail image for Kling 2.5 I2V Pro...")
        tail_png_bytes = _image_tensor_to_png_bytes(tail_images[0])
        tail_image_url = _upload_image(api_key, tail_png_bytes)
        _log(log, f"Tail image upload success: {_truncate_url(tail_image_url)}")

    payload_input: dict[str, Any] = {
        "prompt": prompt,
        "image_url": image_url,
        "duration": duration,
        "cfg_scale": cfg_scale,
    }
    if tail_image_url:
        payload_input["tail_image_url"] = tail_image_url
    if negative_prompt.strip():
        payload_input["negative_prompt"] = negative_prompt

    payload = {"model": MODEL_NAME, "input": payload_input}

    _log(log, "Creating Kling 2.5 I2V Pro task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")
    _log(log, "Check https://kie.ai/logs for request status if needed.")

    effective_timeout = 1000 if timeout_seconds is None else timeout_seconds
    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        10.0,
        effective_timeout,
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
