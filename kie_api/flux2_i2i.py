"""Flux 2 Pro/Flex image-to-image helper."""

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
from .images import _download_image, _image_bytes_to_tensor
from .validation import _validate_prompt

CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_OPTIONS = ["flux-2/pro-image-to-image", "flux-2/flex-image-to-image"]
ASPECT_RATIO_OPTIONS = ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "auto"]
RESOLUTION_OPTIONS = ["1K", "2K"]
PROMPT_MIN_LENGTH = 3
PROMPT_MAX_LENGTH = 5000
MAX_IMAGE_COUNT = 8


def _validate_images(images: torch.Tensor | None) -> torch.Tensor:
    if images is None:
        raise RuntimeError("images input is required.")
    if not isinstance(images, torch.Tensor):
        raise RuntimeError("images input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise RuntimeError("images input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise RuntimeError("images input batch is empty.")
    return images


def _validate_prompt_range(prompt: str) -> None:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    if len(prompt.strip()) < PROMPT_MIN_LENGTH:
        raise RuntimeError(f"Prompt must be at least {PROMPT_MIN_LENGTH} characters.")


def _create_flux_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
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


def run_flux2_i2i(
    *,
    model: str,
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    resolution: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 300,
    log: bool = True,
) -> torch.Tensor:
    """Run Flux 2 Pro/Flex image-to-image job end-to-end."""
    if model not in MODEL_OPTIONS:
        raise RuntimeError("Invalid model. Use the pinned enum options.")
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")

    _validate_prompt_range(prompt)
    images = _validate_images(images)

    api_key = _load_api_key()
    total_images = images.shape[0]
    if total_images > MAX_IMAGE_COUNT and log:
        _log(log, f"More than {MAX_IMAGE_COUNT} images provided ({total_images}); only first {MAX_IMAGE_COUNT} used.")

    upload_count = min(total_images, MAX_IMAGE_COUNT)
    image_urls: list[str] = []
    if upload_count > 0:
        _log(log, f"Uploading {upload_count} image(s) for Flux 2 I2I...")

    for idx in range(upload_count):
        png_bytes = _image_tensor_to_png_bytes(images[idx])
        url = _upload_image(api_key, png_bytes)
        image_urls.append(url)
        _log(log, f"Image {idx + 1} upload success: {_truncate_url(url)}")

    payload = {
        "model": model,
        "input": {
            "input_urls": image_urls,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        },
    }

    _log(log, "Creating Flux 2 I2I task...")
    start_time = time.time()
    task_id, create_response_text = _create_flux_task(api_key, payload)
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
    _log(log, f"Result URLs: {result_urls}")

    _log(log, f"Downloading result image from {result_urls[0]}...")
    image_bytes = _download_image(result_urls[0])
    image_tensor = _image_bytes_to_tensor(image_bytes)
    _log(log, "Image downloaded and decoded.")

    _log_remaining_credits(log, record_data, api_key, _log)
    return image_tensor
