"""Seedance V1 Pro (Fast) image-to-video helper."""

import json
import time
from pathlib import Path
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .http import TransientKieError, requests
from .jobs import _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_prompt
from .video import _download_video, _write_video_to_temp_file


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_NAME = "bytedance/v1-pro-fast-image-to-video"
PROMPT_MAX_LENGTH = 10000
RESOLUTION_OPTIONS = ["720p", "1080p"]
DURATION_OPTIONS = ["5", "10"]


def _validate_options(resolution: str, duration: str) -> None:
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")


def _validate_image_input(images: torch.Tensor | None) -> torch.Tensor:
    if images is None:
        raise RuntimeError("images input is required.")
    if not isinstance(images, torch.Tensor):
        raise RuntimeError("images input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise RuntimeError("images input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise RuntimeError("images input batch is empty.")
    return images


def _create_seedance_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    try:
        response = requests.post(
            CREATE_TASK_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call createTask endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"createTask returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("createTask endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("message") or payload_json.get("msg")
        raise RuntimeError(f"createTask endpoint returned error code {payload_json.get('code')}: {message}")

    task_id = (payload_json.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError("createTask endpoint did not return a taskId.")

    return task_id, response.text


def run_seedancev1pro_fast_i2v_video(
    prompt: str,
    images: torch.Tensor,
    resolution: str,
    duration: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Path:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(resolution, duration)
    images = _validate_image_input(images)

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
    task_id, create_response_text = _create_seedance_task(api_key, payload)
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
    video_path = _write_video_to_temp_mp4(video_bytes)
    _log(log, f"Video saved to {video_path}")

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_path


def run_seedancev1pro_fast_i2v(
    prompt: str,
    images: torch.Tensor,
    resolution: str,
    duration: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Path:
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
                "poll_interval_s": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 60.0, "step": 0.5}),
                "timeout_s": ("INT", {"default": 600, "min": 1, "max": 3600, "step": 1}),
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
        poll_interval_s: float = 1.0,
        timeout_s: int = 600,
    ):
        video_path = run_seedancev1pro_fast_i2v_video(
            prompt=prompt,
            images=images,
            resolution=resolution,
            duration=duration,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (str(video_path),)
