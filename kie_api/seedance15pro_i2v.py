"""Seedance 1.5 Pro image/text-to-video helper."""

import json
import time
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
from .video import _download_video, _video_bytes_to_comfy_video


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_NAME = "bytedance/seedance-1.5-pro"
PROMPT_MAX_LENGTH = 2500
PROMPT_MIN_LENGTH = 3
ASPECT_RATIO_OPTIONS = ["1:1", "21:9", "4:3", "3:4", "16:9", "9:16"]
RESOLUTION_OPTIONS = ["480p", "720p"]
DURATION_OPTIONS = ["4", "8", "12"]


def _validate_prompt_input(prompt: str) -> None:
    if not isinstance(prompt, str):
        raise RuntimeError("Prompt must be a string.")
    if len(prompt) < PROMPT_MIN_LENGTH:
        raise RuntimeError("Prompt must be at least 3 characters long.")
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    try:
        json.dumps({"prompt": prompt})
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Prompt must be JSON-serializable.") from exc


def _validate_options(
    aspect_ratio: str,
    resolution: str,
    duration: str,
    fixed_lens: bool,
    generate_audio: bool,
) -> None:
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if not isinstance(fixed_lens, bool):
        raise RuntimeError("fixed_lens must be a boolean value.")
    if not isinstance(generate_audio, bool):
        raise RuntimeError("generate_audio must be a boolean value.")


def _validate_image_input(images: torch.Tensor | None) -> torch.Tensor | None:
    if images is None:
        return None
    if not isinstance(images, torch.Tensor):
        raise RuntimeError("images input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise RuntimeError("images input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise RuntimeError("images input batch is empty.")
    return images


def _create_seedance15_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
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


def _build_input_urls(api_key: str, images: torch.Tensor | None, log: bool) -> list[str]:
    if images is None:
        return []

    total_images = images.shape[0]
    if total_images > 2:
        _log(log, f"More than 2 images provided ({total_images}); only the first two will be used.")

    upload_count = min(total_images, 2)
    if upload_count > 0:
        _log(log, f"Uploading {upload_count} image(s) for Seedance 1.5 Pro...")

    image_urls: list[str] = []
    for idx in range(upload_count):
        png_bytes = _image_tensor_to_png_bytes(images[idx])
        image_url = _upload_image(api_key, png_bytes)
        image_urls.append(image_url)
        _log(log, f"Image {idx + 1} upload success: {_truncate_url(image_url)}")

    return image_urls


def run_seedance15pro_i2v_video(
    prompt: str,
    images: torch.Tensor | None,
    aspect_ratio: str,
    resolution: str,
    duration: str,
    fixed_lens: bool,
    generate_audio: bool,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> Any:
    _validate_prompt_input(prompt)
    _validate_options(aspect_ratio, resolution, duration, fixed_lens, generate_audio)
    images = _validate_image_input(images)

    api_key = _load_api_key()
    image_urls = _build_input_urls(api_key, images, log)

    if image_urls:
        _log(log, f"Sending {len(image_urls)} image URL(s) to createTask")
    else:
        _log(log, "No images provided; running in text-to-video mode.")

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "input_urls": image_urls,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "duration": duration,
            "fixed_lens": fixed_lens,
            "generate_audio": generate_audio,
        },
    }

    _log(log, "Creating Seedance 1.5 Pro task...")
    start_time = time.time()
    task_id, create_response_text = _create_seedance15_task(api_key, payload)
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


class KIE_Seedance15Pro_I2V:
    HELP = """
KIE Seedance 1.5 Pro (Image-to-Video / Text-to-Video)

Generate a short video clip from a prompt with optional reference images.

Inputs:
- prompt: Text prompt (required)
- images: Optional image batch (first two images used)
- aspect_ratio: 1:1, 21:9, 4:3, 3:4, 16:9, or 9:16
- resolution: 480p or 720p
- duration: 4s, 8s, or 12s
- fixed_lens: Lock camera lens during generation
- generate_audio: Enable audio generation (additional cost)
- poll_interval_s / timeout_s / log

Outputs:
- VIDEO: ComfyUI video output referencing a temporary .mp4 file
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
            },
            "optional": {
                "images": ("IMAGE",),
                "aspect_ratio": ("COMBO", {"options": ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "resolution": ("COMBO", {"options": RESOLUTION_OPTIONS, "default": "720p"}),
                "duration": ("COMBO", {"options": DURATION_OPTIONS, "default": "8"}),
                "fixed_lens": ("BOOLEAN", {"default": False}),
                "generate_audio": ("BOOLEAN", {"default": False}),
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
        images: torch.Tensor | None = None,
        aspect_ratio: str = "1:1",
        resolution: str = "720p",
        duration: str = "8",
        fixed_lens: bool = False,
        generate_audio: bool = False,
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 1000,
    ):
        video_output = run_seedance15pro_i2v_video(
            prompt=prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            duration=duration,
            fixed_lens=fixed_lens,
            generate_audio=generate_audio,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (video_output,)
