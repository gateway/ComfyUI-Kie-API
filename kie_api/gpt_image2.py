"""GPT Image 2 text-to-image and image-to-image helpers."""

import time

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .http import TransientKieError
from .images import _download_image, _image_bytes_to_tensor
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch, _validate_prompt


TEXT_TO_IMAGE_MODEL_NAME = "gpt-image-2-text-to-image"
IMAGE_TO_IMAGE_MODEL_NAME = "gpt-image-2-image-to-image"
ASPECT_RATIO_OPTIONS = ["auto", "1:1", "9:16", "16:9", "4:3", "3:4"]
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
PROMPT_MAX_LENGTH = 20000
MAX_IMAGE_COUNT = 16


def _validate_options(aspect_ratio: str, resolution: str) -> None:
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")
    if aspect_ratio == "auto" and resolution != "1K":
        raise RuntimeError('GPT Image 2 requires resolution "1K" when aspect_ratio is "auto".')
    if aspect_ratio == "1:1" and resolution == "4K":
        raise RuntimeError('GPT Image 2 does not support resolution "4K" with aspect_ratio "1:1".')


def _run_gpt_image2_payload(
    *,
    payload: dict[str, object],
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
    create_label: str,
) -> torch.Tensor:
    api_key = _load_api_key()
    _log(log, f"Creating {create_label} task...")
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
    _log(log, f"Result URLs: {result_urls}")
    _log(log, f"Downloading result image from {result_urls[0]}...")
    image_bytes = _download_image(result_urls[0])
    image_tensor = _image_bytes_to_tensor(image_bytes)
    _log(log, "Image downloaded and decoded.")
    _log_remaining_credits(log, record_data, api_key, _log)
    return image_tensor


def run_gpt_image2_text_to_image(
    *,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 300,
    log: bool = True,
    retry_on_fail: bool = True,
    max_retries: int = 2,
    retry_backoff_s: float = 3.0,
) -> torch.Tensor:
    """Run a GPT Image 2 text-to-image job end-to-end."""
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(aspect_ratio, resolution)

    payload = {
        "model": TEXT_TO_IMAGE_MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        },
    }

    attempts = max_retries + 1 if retry_on_fail else 1
    attempts = max(attempts, 1)
    backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

    for attempt in range(1, attempts + 1):
        try:
            return _run_gpt_image2_payload(
                payload=payload,
                poll_interval_s=poll_interval_s,
                timeout_s=timeout_s,
                log=log,
                create_label="GPT Image 2 text-to-image",
            )
        except TransientKieError:
            if not retry_on_fail or attempt >= attempts:
                raise
            _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
            time.sleep(backoff)

    raise RuntimeError("GPT Image 2 text-to-image job failed after retry attempts.")


def run_gpt_image2_image_to_image(
    *,
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    resolution: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 300,
    log: bool = True,
    retry_on_fail: bool = True,
    max_retries: int = 2,
    retry_backoff_s: float = 3.0,
) -> torch.Tensor:
    """Run a GPT Image 2 image-to-image job end-to-end."""
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(aspect_ratio, resolution)
    images = _validate_image_tensor_batch(images)

    attempts = max_retries + 1 if retry_on_fail else 1
    attempts = max(attempts, 1)
    backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

    for attempt in range(1, attempts + 1):
        try:
            api_key = _load_api_key()
            total_images = images.shape[0]
            if total_images > MAX_IMAGE_COUNT:
                _log(
                    log,
                    f"More than {MAX_IMAGE_COUNT} images provided ({total_images}); "
                    f"only first {MAX_IMAGE_COUNT} used.",
                )

            upload_count = min(total_images, MAX_IMAGE_COUNT)
            image_urls: list[str] = []
            _log(log, f"Uploading {upload_count} image(s) for GPT Image 2 I2I...")
            for idx in range(upload_count):
                png_bytes = _image_tensor_to_png_bytes(images[idx])
                image_url = _upload_image(api_key, png_bytes)
                image_urls.append(image_url)
                _log(log, f"Image {idx + 1} upload success: {_truncate_url(image_url)}")

            payload = {
                "model": IMAGE_TO_IMAGE_MODEL_NAME,
                "input": {
                    "prompt": prompt,
                    "input_urls": image_urls,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                },
            }

            return _run_gpt_image2_payload(
                payload=payload,
                poll_interval_s=poll_interval_s,
                timeout_s=timeout_s,
                log=log,
                create_label="GPT Image 2 image-to-image",
            )
        except TransientKieError:
            if not retry_on_fail or attempt >= attempts:
                raise
            _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
            time.sleep(backoff)

    raise RuntimeError("GPT Image 2 image-to-image job failed after retry attempts.")
