"""
Nano Banana Pro API implementation.

This module contains all logic specific to the KIE Nano Banana Pro model:
- task creation
- polling for completion
- result URL extraction
- image download and decoding

This file is intentionally model-specific and not generic.
"""

import json
import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .http import TransientKieError, requests
from .jobs import _fetch_task_record, _poll_task_until_complete, _should_retry_fail
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .images import _download_image, _image_bytes_to_tensor
from .validation import _validate_prompt

CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
MODEL_NAME = "nano-banana-pro"
ASPECT_RATIO_OPTIONS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "auto"]
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
OUTPUT_FORMAT_OPTIONS = ["png", "jpg"]
PROMPT_MAX_LENGTH = 10000


def _create_nano_banana_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    """Create a nano-banana job and return the task id with raw response text.

    Returns:
        A tuple of (task_id, raw_response_text).
    Raises:
        RuntimeError: If the request fails or the API responds with an error code.
        TransientKieError: If the API responds with retryable errors (429 or >=500).
    """
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


def _create_nanobanana_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    """Backward-compatible alias for node usage."""
    return _create_nano_banana_task(api_key, payload)


def _poll_nanobanana_until_complete(
    api_key: str,
    task_id: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
    start_time: float,
) -> dict[str, Any]:
    """Backward-compatible polling helper used by nodes.

    Returns:
        The task record data dict returned by recordInfo.
    Raises:
        RuntimeError: If the task times out or returns a non-retryable failure.
        TransientKieError: If the task fails with a retryable condition.
    """
    return _poll_task_until_complete(api_key, task_id, poll_interval_s, timeout_s, log, start_time)


def _extract_nanobanana_result_urls(record_data: dict[str, Any]) -> list[str]:
    """Backward-compatible alias for node usage."""
    return _extract_result_urls(record_data)


def _download_nanobanana_image(url: str) -> bytes:
    """Backward-compatible alias for node usage."""
    return _download_image(url)


def run_nanobanana_image_job(
    prompt: str,
    aspect_ratio: str = "auto",
    resolution: str = "1K",
    output_format: str = "png",
    log: bool = True,
    poll_interval_s: float = 10.0,
    timeout_s: int = 300,
    retry_on_fail: bool = True,
    max_retries: int = 2,
    retry_backoff_s: float = 3.0,
    images: torch.Tensor | None = None,
) -> torch.Tensor:
    """Run a Nano Banana Pro image generation job end-to-end.

    Orchestrates the same steps as the ComfyUI node:
    validation → optional reference image upload → task creation → polling → result download → decode.

    Returns:
        A torch tensor of shape (1, H, W, 3) with float values in [0, 1].
    Raises:
        RuntimeError: For validation errors, non-retryable API failures, timeouts, or decoding failures.
        TransientKieError: For retryable API/task failures (used to trigger retries when enabled).
    """
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)

    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")
    if output_format not in OUTPUT_FORMAT_OPTIONS:
        raise RuntimeError("Invalid output_format. Use the pinned enum options.")

    attempts = max_retries + 1 if retry_on_fail else 1
    attempts = max(attempts, 1)
    backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

    for attempt in range(1, attempts + 1):
        start_time = time.time()
        try:
            api_key = _load_api_key()

            image_urls: list[str] = []
            if images is not None:
                if not isinstance(images, torch.Tensor):
                    raise RuntimeError("images input must be a tensor batch.")
                if images.dim() != 4 or images.shape[-1] != 3:
                    raise RuntimeError("images input must have shape [B, H, W, 3].")

                total_images = images.shape[0]
                if total_images > 8 and log:
                    _log(log, f"More than 8 images provided ({total_images}); only first 8 will be used.")

                upload_count = min(total_images, 8)
                if upload_count > 0:
                    _log(log, f"Uploading {upload_count} images...")

                for idx in range(upload_count):
                    try:
                        png_bytes = _image_tensor_to_png_bytes(images[idx])
                        url = _upload_image(api_key, png_bytes)
                        image_urls.append(url)
                        _log(log, f"Image {idx + 1} upload success: {_truncate_url(url)}")
                    except Exception as exc:
                        _log(log, f"Image {idx + 1} upload failed: {exc}")
                        raise

            payload = {
                "model": MODEL_NAME,
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "output_format": output_format,
                    "image_input": image_urls,
                },
            }

            _log(log, f"Sending {len(image_urls)} image URLs to createTask")

            _log(log, "Creating Nano Banana Pro task...")
            task_id, create_response_text = _create_nano_banana_task(api_key, payload)
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
        except TransientKieError:
            if not retry_on_fail or attempt >= attempts:
                raise
            _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
            time.sleep(backoff)
            continue
