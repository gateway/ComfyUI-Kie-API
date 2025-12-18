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
                "poll_interval_s": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 60.0, "step": 0.1}),
                "timeout_s": ("INT", {"default": 300, "min": 1, "max": 3600, "step": 1}),
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
        poll_interval_s: float = 1.0,
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
                "poll_interval_s": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 60.0, "step": 0.1}),
                "timeout_s": ("INT", {"default": 300, "min": 1, "max": 3600, "step": 1}),
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
        poll_interval_s: float = 1.0,
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


NODE_CLASS_MAPPINGS = {
    "KIE_GetRemainingCredits": KIE_GetRemainingCredits,
    "KIE_NanoBananaPro_Image": KIE_NanoBananaPro_Image,
    "KIE_Seedream45_TextToImage": KIE_Seedream45_TextToImage,
    "KIE_Seedream45_Edit": KIE_Seedream45_Edit,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "KIE_GetRemainingCredits": "KIE Get Remaining Credits",
    "KIE_NanoBananaPro_Image": "KIE Nano Banana Pro (Image)",
    "KIE_Seedream45_TextToImage": "KIE Seedream 4.5 Text-To-Image",
    "KIE_Seedream45_Edit": "KIE Seedream 4.5 Edit",
}
