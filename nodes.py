import json
import os
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
from .kie_api.kling25_i2v import (
    DURATION_OPTIONS as KLING25_DURATION_OPTIONS,
    run_kling25_i2v_job,
)
from .kie_api.kling26motion_i2v import (
    CHARACTER_ORIENTATION_OPTIONS as KLING26MOTION_CHARACTER_ORIENTATION_OPTIONS,
    MODE_OPTIONS as KLING26MOTION_MODE_OPTIONS,
    run_kling26motion_i2v_video,
)
from .kie_api.kling26_t2v import (
    ASPECT_RATIO_OPTIONS as KLING26_T2V_ASPECT_RATIO_OPTIONS,
    DURATION_OPTIONS as KLING26_T2V_DURATION_OPTIONS,
    run_kling26_t2v_video,
)
from .kie_api.kling3_video import (
    ASPECT_RATIO_OPTIONS as KLING3_ASPECT_RATIO_OPTIONS,
    DURATION_OPTIONS as KLING3_DURATION_OPTIONS,
    MODE_OPTIONS as KLING3_MODE_OPTIONS,
    build_kling3_element,
    merge_kling3_elements,
    preflight_kling3_payload,
    run_kling3_video,
    run_kling3_video_from_request,
)
from .kie_api.suno_music import MODEL_OPTIONS as SUNO_MODEL_OPTIONS, run_suno_generate
from .kie_api.gemini3_pro_llm import (
    MODEL_OPTIONS as GEMINI3_MODEL_OPTIONS,
    REASONING_EFFORT_OPTIONS as GEMINI3_REASONING_EFFORT_OPTIONS,
    ROLE_OPTIONS as GEMINI3_ROLE_OPTIONS,
    run_gemini3_pro_chat,
)
from .kie_api.flux2_i2i import (
    ASPECT_RATIO_OPTIONS as FLUX2_ASPECT_RATIO_OPTIONS,
    MODEL_OPTIONS as FLUX2_MODEL_OPTIONS,
    RESOLUTION_OPTIONS as FLUX2_RESOLUTION_OPTIONS,
    run_flux2_i2i,
)
from .kie_api.prompt_lists import parse_prompts_json
from .kie_api.grid import slice_grid_tensor
from .kie_api.http import TransientKieError


SYSTEM_PROMPT_MARKER = "system prompt below"
SYSTEM_PROMPT_PLACEHOLDER = "{user_prompt}"
SYSTEM_PROMPT_CATEGORIES = ("images", "videos")


def _system_prompt_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def _scan_system_prompt_templates() -> dict[str, str]:
    prompt_dir = _system_prompt_dir()
    if not os.path.isdir(prompt_dir):
        raise RuntimeError(f"Prompt folder not found: {prompt_dir}")

    templates: dict[str, str] = {}
    for category in SYSTEM_PROMPT_CATEGORIES:
        category_dir = os.path.join(prompt_dir, category)
        if not os.path.isdir(category_dir):
            continue
        for filename in sorted(os.listdir(category_dir)):
            if not filename.lower().endswith(".txt"):
                continue
            if filename.lower() == "readme.txt":
                continue
            path = os.path.join(category_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    lines = handle.read().splitlines()
            except OSError:
                continue

            name: str | None = None
            body_index: int | None = None
            for idx, line in enumerate(lines):
                stripped = line.strip()
                lower = stripped.lower()
                if lower.startswith("name:") and name is None:
                    name = stripped[5:].strip()
                if lower == SYSTEM_PROMPT_MARKER and body_index is None:
                    body_index = idx + 1

            if not name or body_index is None:
                continue

            body = "\n".join(lines[body_index:]).strip()
            if not body:
                continue

            label = f"{category}: {name}"
            templates[label] = body

    return templates


class KIE_GetRemainingCredits:
    HELP = """
KIE Get Remaining Credits

Reads your remaining KIE credits using the API key in config/kie_key.txt.

Inputs:
- (none)

Outputs:
- STRING: data
- INT: Remaining credits
Notes:
- If your key is missing/invalid, this node errors.
"""
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"log": ("BOOLEAN", {"default": True})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("data", "credits_remaining")
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
- images: Source image batch (up to 14 images; all uploaded)
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


class KIE_Kling25_I2V_Pro:
    HELP = """
KIE Kling 2.5 I2V Pro

Generate a short video clip from a prompt and one or two input images using Kling 2.5 Turbo I2V Pro.

Inputs:
- prompt: Text prompt (required)
- first_frame: Source image batch (first image used)
- last_frame: Optional tail image batch (first image used)
- negative_prompt: Optional negative prompt
- duration: 5s or 10s
- cfg_scale: 0.0 to 1.0
- poll_interval_s / timeout_s / log
- retry_on_fail / max_retries / retry_backoff_s

Outputs:
- VIDEO: ComfyUI video output referencing a temporary .mp4 file
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "last_frame": ("IMAGE",),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "duration": ("COMBO", {"options": KLING25_DURATION_OPTIONS, "default": "5"}),
                "cfg_scale": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        first_frame: torch.Tensor,
        prompt: str,
        last_frame: torch.Tensor | None = None,
        negative_prompt: str = "",
        duration: str = "5",
        cfg_scale: float = 0.5,
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 1000,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
    ):
        attempts = max_retries + 1 if retry_on_fail else 1
        attempts = max(attempts, 1)
        backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

        for attempt in range(1, attempts + 1):
            try:
                video_output = run_kling25_i2v_job(
                    image=first_frame,
                    tail_image=last_frame,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    duration=duration,
                    cfg_scale=cfg_scale,
                    timeout_seconds=timeout_s,
                    log=log,
                )
                return (video_output,)
            except TransientKieError:
                if not retry_on_fail or attempt >= attempts:
                    raise
                _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
                time.sleep(backoff)


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
        timeout_s: int = 1000,
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


class KIE_Kling26_T2V:
    HELP = """
KIE Kling 2.6 (Text-to-Video)

Generate a short video clip from a text prompt using Kling 2.6.

Inputs:
- prompt: Text prompt (required)
- sound: Include audio in the output video
- aspect_ratio: 1:1, 16:9, or 9:16
- duration: 5s or 10s
- poll_interval_s / timeout_s / log
- retry_on_fail / max_retries / retry_backoff_s

Outputs:
- VIDEO: ComfyUI video output referencing a temporary .mp4 file
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "sound": ("BOOLEAN", {"default": False}),
                "aspect_ratio": ("COMBO", {"options": KLING26_T2V_ASPECT_RATIO_OPTIONS, "default": "9:16"}),
                "duration": ("COMBO", {"options": KLING26_T2V_DURATION_OPTIONS, "default": "5"}),
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
        sound: bool = False,
        aspect_ratio: str = "9:16",
        duration: str = "5",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 1000,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
    ):
        attempts = max_retries + 1 if retry_on_fail else 1
        attempts = max(attempts, 1)
        backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

        for attempt in range(1, attempts + 1):
            try:
                video_output = run_kling26_t2v_video(
                    prompt=prompt,
                    sound=sound,
                    aspect_ratio=aspect_ratio,
                    duration=duration,
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


class KIE_Kling26Motion_I2V:
    HELP = """
KIE Kling 2.6 Motion-Control (I2V)

Generate a short video clip from a prompt, a reference image, and a motion reference video.

Inputs:
- prompt: Text prompt (required)
- images: Source image batch (first image used)
- video: Motion reference video input (single clip)
- character_orientation: Match character orientation to image or video
- mode: 720p or 1080p output resolution
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
                "video": ("VIDEO",),
            },
            "optional": {
                "character_orientation": (
                    "COMBO",
                    {"options": KLING26MOTION_CHARACTER_ORIENTATION_OPTIONS, "default": "video"},
                ),
                "mode": ("COMBO", {"options": KLING26MOTION_MODE_OPTIONS, "default": "720p"}),
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
        video: object,
        character_orientation: str = "video",
        mode: str = "720p",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 1000,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
    ):
        attempts = max_retries + 1 if retry_on_fail else 1
        attempts = max(attempts, 1)
        backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

        for attempt in range(1, attempts + 1):
            try:
                video_output = run_kling26motion_i2v_video(
                    prompt=prompt,
                    images=images,
                    video=video,
                    character_orientation=character_orientation,
                    mode=mode,
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


class KIE_KlingElements:
    HELP = """
KIE Kling Elements

Build one named Kling element from either images (2-4) or one video.

Inputs:
- name: Element name used by @name in prompts
- description: Optional element description
- images: Optional image batch input (2-4 images)
- video: Optional video input (single clip)
- log: Console logging on/off

Rules:
- Provide exactly one media type: images or video
- Do not connect both images and video to the same element node

Outputs:
- KIE_ELEMENT: Element payload for Kling 3.0
- STRING: JSON preview of the element payload
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "element_name"}),
            },
            "optional": {
                "description": ("STRING", {"default": ""}),
                "images": ("IMAGE",),
                "video": ("VIDEO",),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("KIE_ELEMENT", "STRING")
    RETURN_NAMES = ("element", "data")
    FUNCTION = "build"
    CATEGORY = "kie/helpers"

    def build(
        self,
        name: str,
        description: str = "",
        images: torch.Tensor | None = None,
        video: object | None = None,
        log: bool = True,
    ):
        element_payload = build_kling3_element(
            name=name,
            description=description,
            images=images,
            video=video,
            log=log,
        )
        return (element_payload, json.dumps(element_payload, indent=2, ensure_ascii=False))


class KIE_KlingElementsBatch:
    HELP = """
KIE Kling Elements Batch

Collect up to 9 KIE_ELEMENT payloads into a single KIE_ELEMENTS batch.

Inputs:
- element_1..element_9: Optional KIE_ELEMENT inputs

Outputs:
- KIE_ELEMENTS: Batched elements payload
- STRING: JSON preview of batched elements
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "element_1": ("KIE_ELEMENT",),
                "element_2": ("KIE_ELEMENT",),
                "element_3": ("KIE_ELEMENT",),
                "element_4": ("KIE_ELEMENT",),
                "element_5": ("KIE_ELEMENT",),
                "element_6": ("KIE_ELEMENT",),
                "element_7": ("KIE_ELEMENT",),
                "element_8": ("KIE_ELEMENT",),
                "element_9": ("KIE_ELEMENT",),
            }
        }

    RETURN_TYPES = ("KIE_ELEMENTS", "STRING")
    RETURN_NAMES = ("elements", "data")
    FUNCTION = "batch"
    CATEGORY = "kie/helpers"

    def batch(
        self,
        element_1: dict | None = None,
        element_2: dict | None = None,
        element_3: dict | None = None,
        element_4: dict | None = None,
        element_5: dict | None = None,
        element_6: dict | None = None,
        element_7: dict | None = None,
        element_8: dict | None = None,
        element_9: dict | None = None,
    ):
        elements = merge_kling3_elements(
            element_1,
            element_2,
            element_3,
            element_4,
            element_5,
            element_6,
            element_7,
            element_8,
            element_9,
        )
        if not elements:
            raise RuntimeError("Kling Elements Batch requires at least one element.")
        return (elements, json.dumps(elements, indent=2, ensure_ascii=False))


class KIE_Kling3_Video:
    HELP = """
KIE Kling 3.0 (Video)

Generate video with Kling 3.0 using single-shot or multi-shot prompts.

Inputs:
- mode: std or pro
- aspect_ratio: 1:1, 9:16, 16:9
- duration: 3..15 seconds
- multi_shots: enable multi-shot mode
- prompt: Used in single-shot mode
- shots_text: Used in multi-shot mode, format:
  duration | prompt
  or
  label | duration | prompt
- first_frame: Optional start frame image
- last_frame: Optional end frame image (single-shot only)
- sound: Single-shot only
- element: Optional single KIE_ELEMENT
- elements: Optional KIE_ELEMENTS batch
- payload_data: Optional payload object from preflight (overrides direct inputs)
- log: Console logging on/off

Rules:
- multi_shots=true: last_frame is invalid, sound is invalid
- multi_shots=true: duration is computed from summed shot durations
- If first_frame + last_frame are both used, aspect_ratio is omitted automatically
- @element references in prompt(s) must match provided element names

Outputs:
- VIDEO: ComfyUI video output compatible with SaveVideo
"""
    SHOTS_TEXT_PLACEHOLDER = (
        "shot1 | 4 | Wide cinematic opening with @element_name\n"
        "shot2 | 3 | Medium tracking shot with @element_name\n"
        "shot3 | 3 | Close-up emotional finale with @element_name"
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": ("COMBO", {"options": KLING3_MODE_OPTIONS, "default": "std"}),
                "aspect_ratio": ("COMBO", {"options": KLING3_ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "duration": ("COMBO", {"options": KLING3_DURATION_OPTIONS, "default": "5"}),
                "multi_shots": ("BOOLEAN", {"default": False}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "shots_text": ("STRING", {"multiline": True, "default": cls.SHOTS_TEXT_PLACEHOLDER}),
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "sound": ("BOOLEAN", {"default": True}),
                "element": ("KIE_ELEMENT",),
                "elements": ("KIE_ELEMENTS",),
                "payload_data": ("KIE_KLING3_REQUEST",),
                "request": ("KIE_KLING3_REQUEST",),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        mode: str,
        aspect_ratio: str,
        duration: str,
        multi_shots: bool,
        prompt: str,
        shots_text: str = "",
        first_frame: torch.Tensor | None = None,
        last_frame: torch.Tensor | None = None,
        sound: bool = True,
        element: dict | None = None,
        elements: list[dict] | None = None,
        payload_data: dict | None = None,
        request: dict | None = None,
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 1000,
    ):
        chained_payload = payload_data if payload_data is not None else request
        if chained_payload is not None:
            video_output = run_kling3_video_from_request(
                payload=chained_payload,
                poll_interval_s=poll_interval_s,
                timeout_s=timeout_s,
                log=log,
            )
            return (video_output,)

        merged_elements: list[dict] | None = None
        if elements is not None:
            if not isinstance(elements, list):
                raise RuntimeError("elements input must be a KIE_ELEMENTS payload list.")
            merged_elements = list(elements)
        if element is not None:
            if not isinstance(element, dict):
                raise RuntimeError("element input must be a KIE_ELEMENT payload object.")
            if merged_elements is None:
                merged_elements = []
            merged_elements.append(element)
        if merged_elements is not None:
            merged_elements = merge_kling3_elements(*merged_elements)

        video_output = run_kling3_video(
            mode=mode,
            aspect_ratio=aspect_ratio,
            duration=duration,
            multi_shots=multi_shots,
            sound=sound,
            prompt=prompt,
            shots_text=shots_text,
            first_frame=first_frame,
            last_frame=last_frame,
            elements=merged_elements,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (video_output,)


class KIE_Kling3_Preflight:
    HELP = """
KIE Kling 3.0 Preflight

Validate Kling 3.0 inputs, upload media, and build the exact createTask payload JSON
without submitting a generation task.

Use this node to verify wiring/format before spending generation credits.

Inputs:
- Same as KIE Kling 3.0 (Video)

Outputs:
- KIE_KLING3_REQUEST: validated payload object for chaining into KIE Kling 3.0 (Video)
- STRING: payload_json (exact payload that would be sent to createTask)
- STRING: notes
"""
    SHOTS_TEXT_PLACEHOLDER = (
        "shot1 | 4 | Wide cinematic opening with @element_name\n"
        "shot2 | 3 | Medium tracking shot with @element_name\n"
        "shot3 | 3 | Close-up emotional finale with @element_name"
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": ("COMBO", {"options": KLING3_MODE_OPTIONS, "default": "std"}),
                "aspect_ratio": ("COMBO", {"options": KLING3_ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "duration": ("COMBO", {"options": KLING3_DURATION_OPTIONS, "default": "5"}),
                "multi_shots": ("BOOLEAN", {"default": False}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "shots_text": ("STRING", {"multiline": True, "default": cls.SHOTS_TEXT_PLACEHOLDER}),
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "sound": ("BOOLEAN", {"default": True}),
                "element": ("KIE_ELEMENT",),
                "elements": ("KIE_ELEMENTS",),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("KIE_KLING3_REQUEST", "STRING", "STRING")
    RETURN_NAMES = ("payload_data", "payload_json", "notes")
    FUNCTION = "preflight"
    CATEGORY = "kie/helpers"

    def preflight(
        self,
        mode: str,
        aspect_ratio: str,
        duration: str,
        multi_shots: bool,
        prompt: str,
        shots_text: str = "",
        first_frame: torch.Tensor | None = None,
        last_frame: torch.Tensor | None = None,
        sound: bool = True,
        element: dict | None = None,
        elements: list[dict] | None = None,
        log: bool = True,
    ):
        merged_elements: list[dict] | None = None
        if elements is not None:
            if not isinstance(elements, list):
                raise RuntimeError("elements input must be a KIE_ELEMENTS payload list.")
            merged_elements = list(elements)
        if element is not None:
            if not isinstance(element, dict):
                raise RuntimeError("element input must be a KIE_ELEMENT payload object.")
            if merged_elements is None:
                merged_elements = []
            merged_elements.append(element)
        if merged_elements is not None:
            merged_elements = merge_kling3_elements(*merged_elements)

        payload = preflight_kling3_payload(
            mode=mode,
            aspect_ratio=aspect_ratio,
            duration=duration,
            multi_shots=multi_shots,
            sound=sound,
            prompt=prompt,
            shots_text=shots_text,
            first_frame=first_frame,
            last_frame=last_frame,
            elements=merged_elements,
            log=log,
        )
        payload_input = payload.get("input", {})
        image_urls = payload_input.get("image_urls") or []
        has_aspect_ratio = "aspect_ratio" in payload_input
        element_items = payload_input.get("kling_elements") or []
        element_names = [
            str(item.get("name")).strip()
            for item in element_items
            if isinstance(item, dict) and item.get("name")
        ]

        notes_lines = [
            "VALID: Kling 3.0 preflight checks passed.",
            "No createTask call was made.",
            f"Mode: {payload_input.get('mode')}",
            f"Multi-shots: {payload_input.get('multi_shots')}",
            f"Duration sent: {payload_input.get('duration')}s",
            f"Frame inputs resolved: {len(image_urls)}",
            f"Aspect ratio in payload: {'yes' if has_aspect_ratio else 'no (auto from start/end frames)'}",
            f"Elements provided: {len(element_items)}",
        ]

        if payload_input.get("multi_shots"):
            shot_count = len(payload_input.get("multi_prompt") or [])
            notes_lines.append(f"Shot count: {shot_count}")
        else:
            notes_lines.append(f"Sound enabled: {bool(payload_input.get('sound', False))}")

        if element_names:
            notes_lines.append("Element names: " + ", ".join(element_names))

        notes = "\n".join(notes_lines)
        return (payload, json.dumps(payload, indent=2, ensure_ascii=False), notes)


class KIE_Flux2_I2I:
    HELP = """
KIE Flux 2 (Image-to-Image)

Generate an image from one or more input images using Flux 2 Pro or Flux 2 Flex.

Inputs:
- images: Source image batch (1-8 images; all uploaded)
- prompt: Text prompt (required, 3–5000 chars)
- model: flux-2/pro-image-to-image or flux-2/flex-image-to-image
- aspect_ratio: Output aspect ratio (enum)
- resolution: 1K or 2K
- log: Console logging on/off

Outputs:
- IMAGE: ComfyUI image tensor (BHWC float32 0–1)
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "model": ("COMBO", {"options": FLUX2_MODEL_OPTIONS, "default": "flux-2/pro-image-to-image"}),
                "aspect_ratio": ("COMBO", {"options": FLUX2_ASPECT_RATIO_OPTIONS, "default": "1:1"}),
                "resolution": ("COMBO", {"options": FLUX2_RESOLUTION_OPTIONS, "default": "1K"}),
            },
            "optional": {
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        images: torch.Tensor,
        prompt: str,
        model: str = "flux-2/pro-image-to-image",
        aspect_ratio: str = "1:1",
        resolution: str = "1K",
        log: bool = True,
        poll_interval_s: float = 10.0,
        timeout_s: int = 300,
    ):
        image_tensor = run_flux2_i2i(
            model=model,
            prompt=prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            log=log,
        )
        return (image_tensor,)


class KIE_Gemini3Pro_LLM:
    HELP = """
KIE Gemini (LLM) [Experimental]

Generate text using Gemini 2.5/3 (Pro/Flash).

Inputs:
- model: Gemini model selection (2.5/3 Pro/Flash)
- prompt: Text prompt (required if messages_json is empty)
- role: Message role for the prompt (developer/system/user/assistant/tool)
- images: Optional image batch to include as media content
- video: Optional video input to include as media content
- audio: Optional audio input to include as media content
- messages_json: Optional JSON array of message objects (overrides prompt/role/media)
- stream: Stream responses (SSE); output is returned after completion
- include_thoughts: Include reasoning content in output
- reasoning_effort: low or high
- enable_google_search: Enable the Google Search tool (mutually exclusive with response_format_json)
- response_format_json: Optional JSON schema output format (mutually exclusive with Google Search)
- log: Console logging on/off

Outputs:
- STRING: Assistant response text
- STRING: Reasoning text (empty if include_thoughts is false)
- STRING: data (formatted JSON from last response chunk)
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("COMBO", {"options": GEMINI3_MODEL_OPTIONS, "default": "gemini-3-pro"}),
                "prompt": ("STRING", {"multiline": True}),
                "role": ("COMBO", {"options": GEMINI3_ROLE_OPTIONS, "default": "user"}),
            },
            "optional": {
                "images": ("IMAGE",),
                "video": ("VIDEO",),
                "audio": ("AUDIO",),
                "stream": ("BOOLEAN", {"default": True}),
                "include_thoughts": ("BOOLEAN", {"default": True}),
                "reasoning_effort": ("COMBO", {"options": GEMINI3_REASONING_EFFORT_OPTIONS, "default": "high"}),
                "enable_google_search": ("BOOLEAN", {"default": False}),
                "messages_json": ("STRING", {"multiline": True, "default": ""}),
                "response_format_json": ("STRING", {"multiline": True, "default": ""}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "reasoning", "data")
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        model: str = "gemini-3-pro",
        role: str = "user",
        images: torch.Tensor | None = None,
        video: object | None = None,
        audio: object | None = None,
        messages_json: str = "",
        stream: bool = True,
        include_thoughts: bool = True,
        reasoning_effort: str = "high",
        enable_google_search: bool = False,
        response_format_json: str = "",
        log: bool = True,
    ):
        content, reasoning, raw_json = run_gemini3_pro_chat(
            model=model,
            prompt=prompt,
            messages_json=messages_json,
            role=role,
            images=images,
            video=video,
            audio=audio,
            stream=stream,
            include_thoughts=include_thoughts,
            reasoning_effort=reasoning_effort,
            enable_google_search=enable_google_search,
            response_format_json=response_format_json,
            log=log,
        )
        return (content, reasoning, raw_json)


class KIE_Suno_Music_Basic:
    HELP = """
KIE Suno Music (Basic)

Create a Suno music generation task via KIE API. Returns two AUDIO outputs and record JSON.

Inputs:
- title: Track title (required in custom mode)
- style: Style text (required in custom mode)
- prompt: Text prompt (lyrics in custom mode when instrumental is false)
- custom_mode: Enable custom mode (required)
- instrumental: Instrumental-only mode (required)
- model: V4 / V4_5 / V4_5PLUS / V4_5ALL / V5

Optional:
- negative_tags: Optional tags to avoid
- vocal_gender: m or f (custom mode only)
- log: Console logging on/off

Outputs:
- AUDIO: Generated audio 1
- AUDIO: Generated audio 2
- STRING: data
- IMAGE: Cover image 1
- IMAGE: Cover image 2
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "title": ("STRING", {"default": ""}),
                "style": ("STRING", {"default": "", "multiline": True}),
                "prompt": ("STRING", {"multiline": True}),
                "custom_mode": ("BOOLEAN", {"default": True}),
                "instrumental": ("BOOLEAN", {"default": True}),
                "model": ("COMBO", {"options": SUNO_MODEL_OPTIONS, "default": "V4_5"}),
            },
            "optional": {
                "negative_tags": ("STRING", {"default": ""}),
                "vocal_gender": ("COMBO", {"options": ["male", "female"], "default": "male"}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("AUDIO", "AUDIO", "STRING", "IMAGE", "IMAGE")
    RETURN_NAMES = ("audio_1", "audio_2", "data", "image_1", "image_2")
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        title: str,
        style: str,
        prompt: str,
        custom_mode: bool,
        instrumental: bool,
        model: str,
        negative_tags: str = "",
        vocal_gender: str = "male",
        log: bool = True,
    ):
        gender_value = "m" if vocal_gender == "male" else "f"
        audio_output_1, audio_output_2, raw_json, image_output_1, image_output_2 = run_suno_generate(
            prompt=prompt,
            custom_mode=custom_mode,
            instrumental=instrumental,
            model=model,
            style=style,
            title=title,
            negative_tags=negative_tags,
            vocal_gender=gender_value,
            log=log,
        )
        return (audio_output_1, audio_output_2, raw_json, image_output_1, image_output_2)


class KIE_Suno_Music_Advanced:
    HELP = """
KIE Suno Music (Advanced)

Create a Suno music generation task via KIE API. Returns two AUDIO outputs and record JSON.

Inputs:
- title: Track title (required in custom mode)
- style: Style text (required in custom mode)
- prompt: Text prompt (lyrics in custom mode when instrumental is false)
- custom_mode: Enable custom mode (required)
- instrumental: Instrumental-only mode (required)
- model: V4 / V4_5 / V4_5PLUS / V4_5ALL / V5

Optional:
- negative_tags: Optional tags to avoid
- vocal_gender: m or f (custom mode only)
- style_weight / weirdness_constraint / audio_weight: 0..1
- log: Console logging on/off

Outputs:
- AUDIO: Generated audio 1
- AUDIO: Generated audio 2
- STRING: data
- IMAGE: Cover image 1
- IMAGE: Cover image 2
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "title": ("STRING", {"default": ""}),
                "style": ("STRING", {"default": "", "multiline": True}),
                "prompt": ("STRING", {"multiline": True}),
                "custom_mode": ("BOOLEAN", {"default": True}),
                "instrumental": ("BOOLEAN", {"default": True}),
                "model": ("COMBO", {"options": SUNO_MODEL_OPTIONS, "default": "V4_5"}),
            },
            "optional": {
                "negative_tags": ("STRING", {"default": ""}),
                "vocal_gender": ("COMBO", {"options": ["male", "female"], "default": "male"}),
                "style_weight": ("FLOAT", {"default": 0.65, "min": 0.0, "max": 1.0, "step": 0.01}),
                "weirdness_constraint": ("FLOAT", {"default": 0.65, "min": 0.0, "max": 1.0, "step": 0.01}),
                "audio_weight": ("FLOAT", {"default": 0.65, "min": 0.0, "max": 1.0, "step": 0.01}),
                "log": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("AUDIO", "AUDIO", "STRING", "IMAGE", "IMAGE")
    RETURN_NAMES = ("audio_1", "audio_2", "data", "image_1", "image_2")
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        title: str,
        style: str,
        prompt: str,
        custom_mode: bool,
        instrumental: bool,
        model: str,
        negative_tags: str = "",
        vocal_gender: str = "male",
        style_weight: float = 0.65,
        weirdness_constraint: float = 0.65,
        audio_weight: float = 0.65,
        log: bool = True,
    ):
        gender_value = "m" if vocal_gender == "male" else "f"
        audio_output_1, audio_output_2, raw_json, image_output_1, image_output_2 = run_suno_generate(
            prompt=prompt,
            custom_mode=custom_mode,
            instrumental=instrumental,
            model=model,
            style=style,
            title=title,
            negative_tags=negative_tags,
            vocal_gender=gender_value,
            style_weight=style_weight,
            weirdness_constraint=weirdness_constraint,
            audio_weight=audio_weight,
            log=log,
        )
        return (audio_output_1, audio_output_2, raw_json, image_output_1, image_output_2)


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


class KIEParsePromptGridJSON:
    HELP = """
KIE Parse Prompt Grid JSON (1..9)

Parse LLM JSON containing up to 9 prompts and return each prompt as a separate string output.

Inputs:
- json_text: Raw JSON from an LLM (list or object), wired STRING input
- default_prompt: Fallback prompt if parsing yields no prompts
- max_items: Cap the number of prompts (1..9)
- strict: Raise errors when parsing fails or yields no prompts

Outputs:
- p1..p9: Prompt strings (empty if missing)
- count: Number of prompts parsed
- prompts_list: Raw list of prompts for future automation
"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_text": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "default_prompt": ("STRING", {"default": ""}),
                "max_items": ("INT", {"default": 9, "min": 1, "max": 9}),
                "strict": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "INT",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "prompt 1",
        "prompt 2",
        "prompt 3",
        "prompt 4",
        "prompt 5",
        "prompt 6",
        "prompt 7",
        "prompt 8",
        "prompt 9",
        "count",
        "prompts_list",
        "prompts_list_seq",
    )
    OUTPUT_IS_LIST = (
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
    )
    FUNCTION = "parse"
    CATEGORY = "kie/helpers"

    def parse(
        self,
        json_text: str,
        default_prompt: str = "",
        max_items: int = 9,
        strict: bool = False,
        debug: bool = False,
    ):
        fallback = (default_prompt or "").strip()
        if not (json_text or "").strip() and fallback:
            json_text = fallback

        try:
            prompts = parse_prompts_json(json_text, max_items=max_items, strict=strict, debug=debug)
        except ValueError:
            if strict or not fallback:
                raise
            prompts = [fallback]

        if not prompts and fallback and not strict:
            prompts = [fallback]

        if not prompts:
            if debug:
                parse_prompts_json(json_text, max_items=max_items, strict=True, debug=True)
            raise ValueError(
                "No prompts found in json_text and no default_prompt provided. "
                "Supported keys: prompts (array), prompt1/prompt_1/p1, numeric keys."
            )

        padded = prompts[:9] + [""] * (9 - len(prompts))
        count = len(prompts)
        return (*padded, count, prompts, prompts)


class KIE_SystemPrompt_Selector:
    HELP = """
KIE System Prompt Selector

Combine a user prompt with a system prompt template loaded from the `prompts/` folder.

Template format (in prompts/images or prompts/videos .txt files):
- name: <dropdown label>
- system prompt below
- <system prompt body with optional {user_prompt} placeholder>

Inputs:
- user_prompt: The user prompt text to inject
- system_template: Dropdown from prompt files (images/videos)

Outputs:
- STRING: Combined prompt
"""

    @classmethod
    def INPUT_TYPES(cls):
        try:
            templates = _scan_system_prompt_templates()
            options = sorted(templates.keys())
        except RuntimeError:
            options = []

        if not options:
            options = ["(no templates found)"]

        return {
            "required": {
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "system_template": ("COMBO", {"options": options}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build"
    CATEGORY = "kie/helpers"

    def build(self, user_prompt: str, system_template: str):
        templates = _scan_system_prompt_templates()
        if system_template not in templates:
            raise RuntimeError(
                f"System template '{system_template}' not found in {_system_prompt_dir()}."
            )

        template = templates[system_template]
        user_prompt = (user_prompt or "").strip()
        if SYSTEM_PROMPT_PLACEHOLDER in template:
            combined = template.replace(SYSTEM_PROMPT_PLACEHOLDER, user_prompt)
        elif template and user_prompt:
            combined = f"{template}\n\n{user_prompt}"
        else:
            combined = template or user_prompt

        return (combined,)


NODE_CLASS_MAPPINGS = {
    "KIE_GetRemainingCredits": KIE_GetRemainingCredits,
    "KIE_NanoBananaPro_Image": KIE_NanoBananaPro_Image,
    "KIE_Seedream45_TextToImage": KIE_Seedream45_TextToImage,
    "KIE_Seedream45_Edit": KIE_Seedream45_Edit,
    "KIE_SeedanceV1Pro_Fast_I2V": KIE_SeedanceV1Pro_Fast_I2V,
    "KIE_Seedance15Pro_I2V": KIE_Seedance15Pro_I2V,
    "KIE_Kling25_I2V_Pro": KIE_Kling25_I2V_Pro,
    "KIE_Kling26_I2V": KIE_Kling26_I2V,
    "KIE_Kling26_T2V": KIE_Kling26_T2V,
    "KIE_Kling26Motion_I2V": KIE_Kling26Motion_I2V,
    "KIE_KlingElements": KIE_KlingElements,
    "KIE_KlingElementsBatch": KIE_KlingElementsBatch,
    "KIE_Kling3_Video": KIE_Kling3_Video,
    "KIE_Kling3_Preflight": KIE_Kling3_Preflight,
    "KIE_Flux2_I2I": KIE_Flux2_I2I,
    "KIE_Gemini3Pro_LLM": KIE_Gemini3Pro_LLM,
    "KIE_Suno_Music_Basic": KIE_Suno_Music_Basic,
    "KIE_Suno_Music_Advanced": KIE_Suno_Music_Advanced,
    "KIE_GridSlice": KIE_GridSlice,
    "KIEParsePromptGridJSON": KIEParsePromptGridJSON,
    "KIE_SystemPrompt_Selector": KIE_SystemPrompt_Selector,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "KIE_GetRemainingCredits": "KIE Get Remaining Credits",
    "KIE_NanoBananaPro_Image": "KIE Nano Banana Pro (Image)",
    "KIE_Seedream45_TextToImage": "KIE Seedream 4.5 Text-To-Image",
    "KIE_Seedream45_Edit": "KIE Seedream 4.5 Edit",
    "KIE_SeedanceV1Pro_Fast_I2V": "KIE Seedance V1 Pro Fast (I2V)",
    "KIE_Seedance15Pro_I2V": "KIE Seedance 1.5 Pro (I2V/T2V)",
    "KIE_Kling25_I2V_Pro": "KIE Kling 2.5 I2V Pro",
    "KIE_Kling26_I2V": "KIE Kling 2.6 (I2V)",
    "KIE_Kling26_T2V": "KIE Kling 2.6 (T2V)",
    "KIE_Kling26Motion_I2V": "KIE Kling 2.6 Motion-Control (I2V)",
    "KIE_KlingElements": "KIE Kling Elements",
    "KIE_KlingElementsBatch": "KIE Kling Elements Batch",
    "KIE_Kling3_Video": "KIE Kling 3.0 (Video)",
    "KIE_Kling3_Preflight": "KIE Kling 3.0 Preflight",
    "KIE_Flux2_I2I": "KIE Flux 2 (Image-to-Image)",
    "KIE_Gemini3Pro_LLM": "KIE Gemini (LLM) [Experimental]",
    "KIE_Suno_Music_Basic": "KIE Suno Music (Basic)",
    "KIE_Suno_Music_Advanced": "KIE Suno Music (Advanced)",
    "KIE_GridSlice": "KIE Grid Slice",
    "KIEParsePromptGridJSON": "KIE Parse Prompt Grid JSON (1..9)",
    "KIE_SystemPrompt_Selector": "KIE System Prompt Selector",
}
