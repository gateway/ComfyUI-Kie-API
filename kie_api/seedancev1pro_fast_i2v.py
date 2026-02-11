"""Seedance V1 Pro (Fast) image-to-video helper."""

import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch, _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "bytedance/v1-pro-fast-image-to-video"
PROMPT_MAX_LENGTH = 10000
RESOLUTION_OPTIONS = ["720p", "1080p"]
DURATION_OPTIONS = ["5", "10"]


def _validate_options(resolution: str, duration: str) -> None:
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")


def run_seedancev1pro_fast_i2v_video(
    prompt: str,
    images: torch.Tensor,
    resolution: str,
    duration: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(resolution, duration)
    images = _validate_image_tensor_batch(images)

    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    _log(log, "Uploading source image for Seedance I2V...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "image_url": image_url,
            "resolution": resolution,
            "duration": duration,
        },
    }

    _log(log, "Creating Seedance V1 Pro Fast I2V task...")
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
    video_url = result_urls[0]
    _log(log, f"Downloading video result from {video_url}...")

    video_bytes = _download_video(video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output


def run_seedancev1pro_fast_i2v(
    prompt: str,
    images: torch.Tensor,
    resolution: str,
    duration: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    """Backward-compatible alias."""
    return run_seedancev1pro_fast_i2v_video(
        prompt,
        images,
        resolution,
        duration,
        poll_interval_s,
        timeout_s,
        log,
    )


class KIE_SeedanceV1Pro_Fast_I2V:
    HELP = """
KIE Seedance V1 Pro Fast (Image-to-Video)

Transform a single image plus prompt into an mp4 animation using ByteDance's fast Seedance V1 Pro pipeline.

Inputs:
- prompt (STRING)
- images (IMAGE tensor, first frame used)
- resolution: 720p or 1080p
- duration: 5s or 10s
- poll_interval_s / timeout_s / log

Outputs:
- VIDEO: Path to a temporary .mp4 file.
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "images": ("IMAGE",),
            },
            "optional": {
                "resolution": ("COMBO", {"options": RESOLUTION_OPTIONS, "default": "720p"}),
                "duration": ("COMBO", {"options": DURATION_OPTIONS, "default": "5"}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        images: torch.Tensor,
        resolution: str = "720p",
        duration: str = "5",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 2000,
    ):
        video_output = run_seedancev1pro_fast_i2v_video(
            prompt=prompt,
            images=images,
            resolution=resolution,
            duration=duration,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (video_output,)
