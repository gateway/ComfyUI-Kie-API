import time

import torch

from .kie_api.auth import _load_api_key
from .kie_api.credits import _fetch_remaining_credits, _log_remaining_credits
from .kie_api.http import TransientKieError
from .kie_api.nanobanana import (
    ASPECT_RATIO_OPTIONS,
    MODEL_NAME,
    OUTPUT_FORMAT_OPTIONS,
    RESOLUTION_OPTIONS,
    _create_nano_banana_task,
    _download_image,
    _extract_result_urls,
    _image_bytes_to_tensor,
    _log,
    _poll_task_until_complete,
    _validate_prompt,
)
from .kie_api.upload import (
    _image_tensor_to_png_bytes,
    _truncate_url,
    _upload_image,
)


class KIE_GetRemainingCredits:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"log": ("BOOLEAN", {"default": True})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("raw_json", "credits_remaining")
    FUNCTION = "get_remaining_credits"
    CATEGORY = "kie/api"

    def get_remaining_credits(self, log: bool):
        _log(log, "Requesting remaining credits...")
        api_key = _load_api_key()
        raw_json, credits_remaining = _fetch_remaining_credits(api_key)
        _log(log, f"Credits remaining: {credits_remaining}")
        return (raw_json, credits_remaining)


class KIE_NanoBananaPro_Image:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"prompt": ("STRING", {"multiline": True})},
            "optional": {
                "images": ("IMAGE",),
                "aspect_ratio": ("COMBO", {"options": ASPECT_RATIO_OPTIONS, "default": "auto"}),
                "resolution": ("COMBO", {"options": RESOLUTION_OPTIONS, "default": "1K"}),
                "output_format": ("COMBO", {"options": OUTPUT_FORMAT_OPTIONS, "default": "png"}),
                "log": ("BOOLEAN", {"default": True}),
                "poll_interval_s": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 60.0, "step": 0.1}),
                "timeout_s": ("INT", {"default": 300, "min": 1, "max": 3600, "step": 1}),
                "retry_on_fail": ("BOOLEAN", {"default": True}),
                "max_retries": ("INT", {"default": 2, "min": 0, "max": 10, "step": 1}),
                "retry_backoff_s": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 300.0, "step": 0.5}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "auto",
        resolution: str = "1K",
        output_format: str = "png",
        log: bool = True,
        poll_interval_s: float = 1.0,
        timeout_s: int = 300,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
        images: torch.Tensor | None = None,
    ):
        _validate_prompt(prompt)

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

                record_data, _raw_json, _message_field, elapsed_text = _poll_task_until_complete(
                    api_key,
                    task_id,
                    poll_interval_s,
                    timeout_s,
                    log,
                    start_time,
                )
                result_urls = _extract_result_urls(record_data)
                _log(log, f"Result URLs: {result_urls}")

                _log(log, f"Downloading result image from {result_urls[0]} (elapsed={elapsed_text})...")
                image_bytes = _download_image(result_urls[0])
                image_tensor = _image_bytes_to_tensor(image_bytes)
                _log(log, "Image downloaded and decoded.")

                _log_remaining_credits(log, record_data, api_key, _log)

                return (image_tensor,)
            except TransientKieError as exc:
                if not retry_on_fail or attempt >= attempts:
                    raise
                _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
                time.sleep(backoff)
                continue


NODE_CLASS_MAPPINGS = {
    "KIE_GetRemainingCredits": KIE_GetRemainingCredits,
    "KIE_NanoBananaPro_Image": KIE_NanoBananaPro_Image,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "KIE_GetRemainingCredits": "KIE Get Remaining Credits",
    "KIE_NanoBananaPro_Image": "KIE Nano Banana Pro (Image)",
}
