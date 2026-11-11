"""GPT Image 2 / 2.5 / 2.6 text-to-image and image-to-image helpers."""

import time

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .http import TransientKieError
from .images import _download_image
from .gpt_image_media import collect_results, prepare_edit_guide
from .gpt_image_options import DEFAULT_MODEL, MAX_IMAGE_COUNT, build_gpt_image_payload
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch


def _run_gpt_image2_payload(
    *,
    payload: dict[str, object],
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
    create_label: str,
) -> tuple:
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
    import folder_paths

    result = collect_results(
        ((url, _download_image(url)) for url in result_urls),
        task_id=task_id, output_format=payload["input"].get("output_format"),
        output_dir=folder_paths.get_output_directory(),
    )
    _log(log, "Original output files saved and decoded.")
    _log_remaining_credits(log, record_data, api_key, _log)
    return result


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
    model: str = DEFAULT_MODEL,
    background: str = "opaque",
    **options,
) -> tuple:
    """Run the selected GPT Image text-to-image model; return image frames, masks, original paths, SVG text, and metadata."""
    payload = build_gpt_image_payload(
        model=model, mode="text-to-image", prompt=prompt,
        aspect_ratio=aspect_ratio, resolution=resolution, background=background, **options,
    )

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
                create_label=f"{model} text-to-image",
            )
        except TransientKieError:
            if not retry_on_fail or attempt >= attempts:
                raise
            _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
            time.sleep(backoff)

    raise RuntimeError(f"{model} text-to-image job failed after retry attempts.")


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
    model: str = DEFAULT_MODEL,
    background: str = "opaque",
    mask=None,
    markup=None,
    markup_mask=None,
    **options,
) -> tuple:
    """Run the selected GPT Image editing model; return image frames, masks, original paths, SVG text, and metadata."""
    payload = build_gpt_image_payload(
        model=model, mode="image-to-image", prompt=prompt,
        aspect_ratio=aspect_ratio, resolution=resolution, background=background, **options,
    )
    images = _validate_image_tensor_batch(images)
    if min(images.shape[1:3]) <= 0 or not torch.isfinite(images).all() or (images < 0).any() or (images > 1).any():
        raise RuntimeError("Source images must have nonzero dimensions and finite values between 0 and 1.")
    guide = prepare_edit_guide(
        images=images, model=model, output_format=payload["input"].get("output_format", "png"),
        mask=mask, markup=markup, markup_mask=markup_mask,
    )
    total_images = images.shape[0]
    if total_images > MAX_IMAGE_COUNT and model != DEFAULT_MODEL:
        raise RuntimeError(f"{model} accepts at most {MAX_IMAGE_COUNT} source images; received {total_images}.")

    attempts = max_retries + 1 if retry_on_fail else 1
    attempts = max(attempts, 1)
    backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

    for attempt in range(1, attempts + 1):
        try:
            api_key = _load_api_key()
            if total_images > MAX_IMAGE_COUNT:
                _log(
                    log,
                    f"More than {MAX_IMAGE_COUNT} images provided ({total_images}); "
                    f"only first {MAX_IMAGE_COUNT} used.",
                )

            upload_count = min(total_images, MAX_IMAGE_COUNT)
            image_urls: list[str] = []
            _log(log, f"Uploading {upload_count} image(s) for {model} I2I...")
            for idx in range(upload_count):
                png_bytes = _image_tensor_to_png_bytes(images[idx])
                image_url = _upload_image(api_key, png_bytes)
                image_urls.append(image_url)
                _log(log, f"Image {idx + 1} upload success: {_truncate_url(image_url)}")

            payload["input"]["input_urls"] = image_urls
            if guide is not None:
                field, png_bytes = guide
                payload["input"][field] = _upload_image(api_key, png_bytes)

            return _run_gpt_image2_payload(
                payload=payload,
                poll_interval_s=poll_interval_s,
                timeout_s=timeout_s,
                log=log,
                create_label=f"{model} image-to-image",
            )
        except TransientKieError:
            if not retry_on_fail or attempt >= attempts:
                raise
            _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
            time.sleep(backoff)

    raise RuntimeError(f"{model} image-to-image job failed after retry attempts.")
