"""Seedream 5.0 Flash image-to-image helper.

Implements the Seedream 5.0 Flash image-to-image endpoint documented at
https://docs.kie.ai/market/seedream/5-flash-image-to-image

Model id: `seedream/5-flash-image-to-image`.

Flash differences versus Pro/Lite: resolution is expressed as a `size` tier
(`1K` / `1.5K` / `2K`) instead of the `quality` enum, and it is the fast/cheap
tier of the family. Up to 10 reference images.
"""

import time
from typing import Any

import torch

from .auth import _load_api_key
from .images import _download_image, _image_bytes_to_tensor
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch, _validate_prompt


MODEL_NAME = "seedream/5-flash-image-to-image"
ASPECT_RATIO_OPTIONS = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"]
# Flash expresses resolution as a tier instead of the Pro/Lite `quality` enum.
SIZE_OPTIONS = ["1K", "1.5K", "2K"]
OUTPUT_FORMAT_OPTIONS = ["png", "jpeg"]
PROMPT_MAX_LENGTH = 3000
MAX_IMAGE_COUNT = 10


def _validate_options(aspect_ratio: str, size: str, output_format: str) -> None:
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if size not in SIZE_OPTIONS:
        raise RuntimeError("Invalid size. Use the pinned enum options.")
    if output_format not in OUTPUT_FORMAT_OPTIONS:
        raise RuntimeError("Invalid output_format. Use the pinned enum options.")


def run_seedream5_flash_image_to_image(
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    size: str,
    output_format: str,
    nsfw_checker: bool,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> torch.Tensor:
    """Run a Seedream 5.0 Flash image-to-image (edit) job.

    Args:
        prompt: Edit instruction text.
        images: ComfyUI IMAGE tensor batch (B, H, W, 3), up to 10 images.
        aspect_ratio: Output aspect ratio (spec-defined enum).
        size: Output resolution tier.
        output_format: Output image format.
        nsfw_checker: Enable KIE content filtering.
        poll_interval_s: Seconds between status polls.
        timeout_s: Maximum seconds to wait for completion.
        log: Enable verbose logging.

    Returns:
        ComfyUI IMAGE tensor (1, H, W, 3) float32 in [0, 1].
    """
    prompt = (prompt or "").strip()
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(aspect_ratio, size, output_format)
    images = _validate_image_tensor_batch(images)

    upload_count = images.shape[0]
    if upload_count > MAX_IMAGE_COUNT:
        raise RuntimeError(f"Too many reference images: {upload_count} provided, {MAX_IMAGE_COUNT} allowed.")

    api_key = _load_api_key()
    image_urls: list[str] = []
    if upload_count > 0:
        _log(log, f"Uploading {upload_count} reference image(s)...")

    for idx in range(upload_count):
        png_bytes = _image_tensor_to_png_bytes(images[idx])
        image_url = _upload_image(api_key, png_bytes)
        image_urls.append(image_url)
        _log(log, f"Image {idx + 1} upload success: {_truncate_url(image_url)}")

    payload: dict[str, Any] = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "image_urls": image_urls,
            "aspect_ratio": aspect_ratio,
            "size": size,
            "output_format": output_format,
            "nsfw_checker": nsfw_checker,
        },
    }

    _log(log, f"Sending {len(image_urls)} image URL(s) to createTask")
    _log(log, "Creating Seedream 5.0 Flash image-to-image task...")
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

    return image_tensor
