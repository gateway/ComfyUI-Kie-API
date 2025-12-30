import time

import torch

from .kie_api.auth import _load_api_key
from .kie_api.credits import _fetch_remaining_credits, _log_remaining_credits
from .kie_api.nanobanana import (
    ASPECT_RATIO_OPTIONS,
    OUTPUT_FORMAT_OPTIONS,
    RESOLUTION_OPTIONS,
    _log,
    run_nanobanana_image_job,
)
from .kie_api.seedream45_t2i import (
    ASPECT_RATIO_OPTIONS as SEEDREAM_ASPECT_RATIO_OPTIONS,
    QUALITY_OPTIONS as SEEDREAM_QUALITY_OPTIONS,
    run_seedream45_text_to_image,
)
from .kie_api.seedream45_edit import (
    ASPECT_RATIO_OPTIONS as SEEDREAM_EDIT_ASPECT_RATIO_OPTIONS,
    QUALITY_OPTIONS as SEEDREAM_EDIT_QUALITY_OPTIONS,
    run_seedream45_edit,
)
from .kie_api.seedancev1pro_fast_i2v import KIE_SeedanceV1Pro_Fast_I2V
from .kie_api.seedance15pro_i2v import KIE_Seedance15Pro_I2V
from .kie_api.kling26_i2v import (
    DURATION_OPTIONS as KLING26_DURATION_OPTIONS,
    run_kling26_i2v_video,
)
from .kie_api.grid import slice_grid_tensor
from .kie_api.http import TransientKieError


class KIE_GetRemainingCredits:
    HELP = """
KIE Get Remaining Credits

Reads your remaining KIE credits using the API key in config/kie_key.txt.

Inputs:
- (none)

Outputs:
- INT: Remaining credits
Notes:
- If your key is missing/invalid, this node errors.
"""
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
    HELP = """
KIE Nano Banana Pro (Image)

Generate an image using Nano Banana Pro. Optionally provide up to 8 reference images.

Inputs:
- prompt: Text prompt (required)
- images: Optional reference images (max 8)
- aspect_ratio: Output aspect ratio
- resolution: 1K / 2K / 4K
- output_format: png / jpg
- poll_interval_s: Status check interval
- timeout_s: Max wait time
- log: Console logging on/off

Outputs:
- IMAGE: ComfyUI image tensor (BHWC float32 0–1)
"""
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
        poll_interval_s: float = 10.0,
        timeout_s: int = 300,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
        images: torch.Tensor | None = None,
    ):
        image_tensor = run_nanobanana_image_job(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            log=log,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            retry_on_fail=retry_on_fail,
            max_retries=max_retries,
            retry_backoff_s=retry_backoff_s,
            images=images,
        )
        return (image_tensor,)


class KIE_Seedream45_TextToImage:
    HELP = """
KIE Seedream 4.5 Text-To-Image

Generate an image from a prompt (no reference images required).

Inputs:
- prompt: Text prompt (required)
- aspect_ratio / resolution / output_format
- poll_interval_s / timeout_s / log

Outputs:
- IMAGE: ComfyUI image tensor (BHWC float32 0–1)
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
            },
            "optional": {
                "aspect_ratio": ("COMBO", {"options": SEEDREAM_ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "quality": ("COMBO", {"options": SEEDREAM_QUALITY_OPTIONS, "default": "basic"}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        quality: str = "basic",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 300,
    ):
        image_tensor = run_seedream45_text_to_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            quality=quality,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (image_tensor,)


class KIE_Seedream45_Edit:
    HELP = """
KIE Seedream 4.5 Edit

Edit an input image using Seedream 4.5.

Inputs:
- prompt: Edit prompt (required)
- images: Source image batch (first image used)
- aspect_ratio / quality
- poll_interval_s / timeout_s / log

Outputs:
- IMAGE: ComfyUI image tensor (BHWC float32 0–1)
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "images": ("IMAGE",),
            },
            "optional": {
                "aspect_ratio": ("COMBO", {"options": SEEDREAM_EDIT_ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "quality": ("COMBO", {"options": SEEDREAM_EDIT_QUALITY_OPTIONS, "default": "basic"}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        images: torch.Tensor,
        aspect_ratio: str = "1:1",
        quality: str = "basic",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 300,
    ):
        image_tensor = run_seedream45_edit(
            prompt=prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            quality=quality,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (image_tensor,)


class KIE_Kling26_I2V:
    HELP = """
KIE Kling 2.6 (Video)

Generate a short video clip from a prompt and a single input image using Kling 2.6.

Inputs:
- prompt: Text prompt (required)
- images: Source image batch (first image used)
- duration: 5s or 10s
- sound: Include audio in the output video
- poll_interval_s / timeout_s / log
- retry_on_fail / max_retries / retry_backoff_s

Outputs:
- VIDEO: ComfyUI video output referencing a temporary .mp4 file
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "images": ("IMAGE",),
            },
            "optional": {
                "duration": ("COMBO", {"options": KLING26_DURATION_OPTIONS, "default": "5"}),
                "sound": ("BOOLEAN", {"default": False}),
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
        images: torch.Tensor,
        duration: str = "5",
        sound: bool = False,
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 900,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
    ):
        attempts = max_retries + 1 if retry_on_fail else 1
        attempts = max(attempts, 1)
        backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

        for attempt in range(1, attempts + 1):
            try:
                video_output = run_kling26_i2v_video(
                    prompt=prompt,
                    images=images,
                    duration=duration,
                    sound=sound,
                    poll_interval_s=poll_interval_s,
                    timeout_s=timeout_s,
                    log=log,
                )
                return (video_output,)
            except TransientKieError:
                if not retry_on_fail or attempt >= attempts:
                    raise
                _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
                time.sleep(backoff)


class KIE_GridSlice:
    HELP = """
KIE Grid Slice

Slice a single grid image into equal tiles, optionally cropping borders and removing gutters.

Inputs:
- IMAGE: Grid image batch (BHWC float32 0–1)
- grid: 2x2, 2x3, or 3x3 layout
- outer_crop_px: Pixels to trim from each side before slicing
- gutter_px: Pixels to remove between tiles inside the grid
- order: Tile ordering (row-major or column-major)
- process_batch: Process only the first image or all images in the batch
- log: Console logging on/off

Outputs:
- IMAGE: Tile batch (4, 6, or 9 per processed image)
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "grid": ("COMBO", {"options": ["2x2", "2x3", "3x3"], "default": "2x2"}),
                "outer_crop_px": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "gutter_px": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "order": ("COMBO", {"options": ["row-major", "column-major"], "default": "row-major"}),
                "process_batch": ("COMBO", {"options": ["first", "all"], "default": "first"}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("tiles",)
    FUNCTION = "slice"
    CATEGORY = "kie/helpers"

    def slice(
        self,
        image: torch.Tensor,
        grid: str = "2x2",
        outer_crop_px: int = 0,
        gutter_px: int = 0,
        order: str = "row-major",
        process_batch: str = "first",
        log: bool = True,
    ):
        tile_batch = slice_grid_tensor(
            image=image,
            grid=grid,
            outer_crop_px=outer_crop_px,
            gutter_px=gutter_px,
            order=order,
            process_batch=process_batch,
            log=log,
        )
        return (tile_batch,)


NODE_CLASS_MAPPINGS = {
    "KIE_GetRemainingCredits": KIE_GetRemainingCredits,
    "KIE_NanoBananaPro_Image": KIE_NanoBananaPro_Image,
    "KIE_Seedream45_TextToImage": KIE_Seedream45_TextToImage,
    "KIE_Seedream45_Edit": KIE_Seedream45_Edit,
    "KIE_SeedanceV1Pro_Fast_I2V": KIE_SeedanceV1Pro_Fast_I2V,
    "KIE_Seedance15Pro_I2V": KIE_Seedance15Pro_I2V,
    "KIE_Kling26_I2V": KIE_Kling26_I2V,
    "KIE_GridSlice": KIE_GridSlice,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "KIE_GetRemainingCredits": "KIE Get Remaining Credits",
    "KIE_NanoBananaPro_Image": "KIE Nano Banana Pro (Image)",
    "KIE_Seedream45_TextToImage": "KIE Seedream 4.5 Text-To-Image",
    "KIE_Seedream45_Edit": "KIE Seedream 4.5 Edit",
    "KIE_SeedanceV1Pro_Fast_I2V": "KIE Seedance V1 Pro Fast (I2V)",
    "KIE_Seedance15Pro_I2V": "KIE Seedance 1.5 Pro (I2V/T2V)",
    "KIE_Kling26_I2V": "KIE Kling 2.6 (I2V/T2V)",
    "KIE_GridSlice": "KIE Grid Slice",
}
