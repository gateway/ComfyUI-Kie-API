"""Seedream 4.5 image edit helper.

Implements the Seedream 4.5 edit workflow as documented in
`docs/KIE_API_SEEDREAM_45_EDIT_SPEC.md`.

This module:
- validates inputs
- uploads the input image
- creates a task
- polls until completion (shared helper)
- downloads and decodes the resulting image (shared helper)
"""

import json
import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .http import TransientKieError, requests
from .images import _download_image, _image_bytes_to_tensor
from .jobs import _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_prompt


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_NAME = "seedream/4.5-edit"
ASPECT_RATIO_OPTIONS = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"]
QUALITY_OPTIONS = ["basic", "high"]
PROMPT_MAX_LENGTH = 3000


def _validate_options(aspect_ratio: str, quality: str) -> None:
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if quality not in QUALITY_OPTIONS:
        raise RuntimeError("Invalid quality. Use the pinned enum options.")


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


def _create_seedream45_edit_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
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


def run_seedream45_edit(
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    quality: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> torch.Tensor:
    """Run a Seedream 4.5 image edit job.

    Args:
        prompt: Edit instruction text.
        images: ComfyUI IMAGE tensor batch (B, H, W, 3).
        aspect_ratio: Output aspect ratio (spec-defined enum).
        quality: Output quality (spec-defined enum).
        poll_interval_s: Seconds between status polls.
        timeout_s: Maximum seconds to wait for completion.
        log: Enable verbose logging.

    Returns:
        ComfyUI IMAGE tensor (1, H, W, 3) float32 in [0, 1].

    Raises:
        RuntimeError: For validation errors or non-retryable API/task failures.
        TransientKieError: For retryable API/task failures.
    """
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(aspect_ratio, quality)
    images = _validate_image_input(images)

    api_key = _load_api_key()

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    _log(log, "Uploading edit input image...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Input image upload success: {_truncate_url(image_url)}")

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "image_urls": [image_url],
            "aspect_ratio": aspect_ratio,
            "quality": quality,
        },
    }

    _log(log, "Creating Seedream 4.5 edit task...")
    start_time = time.time()
    task_id, create_response_text = _create_seedream45_edit_task(api_key, payload)
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
