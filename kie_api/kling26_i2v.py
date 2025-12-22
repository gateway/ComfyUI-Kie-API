"""Kling 2.6 image-to-video helper."""

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
from .video import _download_video, _video_path_to_comfy_video_output, _write_video_to_temp_file


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_NAME = "kling-2.6/image-to-video"
PROMPT_MAX_LENGTH = 1000
DURATION_OPTIONS = ["5", "10"]


def _validate_options(duration: str, sound: bool) -> None:
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if not isinstance(sound, bool):
        raise RuntimeError("sound must be a boolean value.")


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


def _create_kling_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
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


def run_kling26_i2v_video(
    prompt: str,
    images: torch.Tensor,
    duration: str = "5",
    sound: bool = False,
    poll_interval_s: float = 1.0,
    timeout_s: int = 600,
    log: bool = True,
) -> dict:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(duration, sound)
    images = _validate_image_input(images)

    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    _log(log, "Uploading source image for Kling 2.6 I2V...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "image_urls": [image_url],
            "sound": sound,
            "duration": duration,
        },
    }

    _log(log, "Creating Kling 2.6 I2V task...")
    start_time = time.time()
    task_id, create_response_text = _create_kling_task(api_key, payload)
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
    _log(True, f"Video result URL: {video_url}")
    _log(log, f"Downloading video result from {video_url}...")

    video_bytes = _download_video(video_url)
    video_path = _write_video_to_temp_file(video_bytes)
    _log(log, f"Video saved to {video_path}")

    _log_remaining_credits(log, record_data, api_key, _log)
    return _video_path_to_comfy_video_output(video_path)


def run_kling26_i2v(
    prompt: str,
    images: torch.Tensor,
    duration: str = "5",
    sound: bool = False,
    poll_interval_s: float = 1.0,
    timeout_s: int = 600,
    log: bool = True,
) -> dict:
    """Backward-compatible alias for existing imports."""
    return run_kling26_i2v_video(
        prompt=prompt,
        images=images,
        duration=duration,
        sound=sound,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
