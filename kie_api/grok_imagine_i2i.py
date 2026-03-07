"""Grok Imagine image-to-image helper."""

import time

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .images import _download_images_as_batch
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch


MODEL_NAME = "grok-imagine/image-to-image"
PROMPT_MAX_LENGTH = 390000


def _validate_optional_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise RuntimeError("prompt must be a string.")

    prompt_value = prompt or ""
    if len(prompt_value) > PROMPT_MAX_LENGTH:
        raise RuntimeError(f"Prompt exceeds the maximum length of {PROMPT_MAX_LENGTH} characters.")

    return prompt_value


def run_grok_imagine_i2i(
    images: torch.Tensor,
    prompt: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> tuple[torch.Tensor, str]:
    images = _validate_image_tensor_batch(images)
    prompt_value = _validate_optional_prompt(prompt)

    if images.shape[0] > 1:
        _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

    api_key = _load_api_key()

    _log(log, "Uploading source image for Grok Imagine I2I...")
    png_bytes = _image_tensor_to_png_bytes(images[0])
    image_url = _upload_image(api_key, png_bytes)
    _log(log, f"Image upload success: {_truncate_url(image_url)}")

    input_payload: dict[str, object] = {
        "image_urls": [image_url],
    }
    if prompt_value.strip():
        input_payload["prompt"] = prompt_value

    payload = {
        "model": MODEL_NAME,
        "input": input_payload,
    }

    _log(log, "Creating Grok Imagine I2I task...")
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
    _log(log, f"Result URLs: {result_urls}")
    _log(log, f"Downloading {len(result_urls)} Grok Imagine I2I result image(s)...")
    image_batch = _download_images_as_batch(result_urls)
    _log(log, "Images downloaded and decoded.")

    _log_remaining_credits(log, record_data, api_key, _log)
    return image_batch, task_id
