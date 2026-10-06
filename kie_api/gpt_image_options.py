"""Pinned Kie GPT Image contracts, shared by validation and widget metadata."""

DEFAULT_MODEL = "GPT Image 2"
MODEL_PREFIXES = {
    DEFAULT_MODEL: "gpt-image-2",
    "GPT Image 2.5 Flare": "gpt-image-2-5-flare",
    "GPT Image 2.5 Sunburst": "gpt-image-2-5-sunburst",
}
MODEL_OPTIONS = list(MODEL_PREFIXES)
LEGACY_ASPECT_RATIOS = ["auto", "1:1", "9:16", "16:9", "4:3", "3:4"]
ASPECT_RATIO_OPTIONS = [
    *LEGACY_ASPECT_RATIOS, "3:2", "2:3", "21:9", "27:16", "16:27", "9:8", "8:9",
]
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
BACKGROUND_OPTIONS = ["opaque", "transparent", "auto"]
ONE_K_ONLY_RATIOS = {"27:16", "16:27", "9:8", "8:9"}
PROMPT_MAX_LENGTH = 20000
MAX_IMAGE_COUNT = 16


def model_widget_options() -> dict:
    """Expose the same compatibility rules to the frontend without a second table."""
    options = {}
    for model in MODEL_OPTIONS:
        legacy = model == DEFAULT_MODEL
        ratios = LEGACY_ASPECT_RATIOS if legacy else ASPECT_RATIO_OPTIONS
        resolutions = {}
        for ratio in ratios:
            if (legacy and ratio == "auto") or (not legacy and ratio in ONE_K_ONLY_RATIOS):
                resolutions[ratio] = ["1K"]
            elif legacy and ratio == "1:1":
                resolutions[ratio] = ["1K", "2K"]
            else:
                resolutions[ratio] = list(RESOLUTION_OPTIONS)
        options[model] = {
            "aspect_ratios": list(ratios),
            "resolutions": resolutions,
            "backgrounds": ["opaque"] if legacy else list(BACKGROUND_OPTIONS),
        }
    return options


def build_gpt_image_payload(
    *, model: str, mode: str, prompt: str, aspect_ratio: str,
    resolution: str, background: str,
) -> dict:
    """Validate before any upload/submission; I2I URLs are attached after upload."""
    if model not in MODEL_PREFIXES:
        raise RuntimeError(f"Unknown GPT Image model: {model!r}. Choose a model from the dropdown.")
    if mode not in ("text-to-image", "image-to-image"):
        raise RuntimeError(f"Unknown GPT Image mode: {mode!r}.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RuntimeError("Prompt is required.")
    if len(prompt) > PROMPT_MAX_LENGTH:
        raise RuntimeError(f"Prompt exceeds the maximum length of {PROMPT_MAX_LENGTH} characters.")
    options = model_widget_options()[model]
    if aspect_ratio not in options["aspect_ratios"]:
        raise RuntimeError(f"{model} does not support aspect_ratio {aspect_ratio!r}.")
    allowed = options["resolutions"][aspect_ratio]
    if resolution not in allowed:
        raise RuntimeError(
            f"{model} with aspect_ratio {aspect_ratio!r} requires resolution: {', '.join(allowed)}."
        )
    if background not in options["backgrounds"]:
        raise RuntimeError(f"{model} supports background: {', '.join(options['backgrounds'])}.")
    inputs = {"prompt": prompt, "aspect_ratio": aspect_ratio, "resolution": resolution}
    if model != DEFAULT_MODEL:
        inputs["background"] = background
    return {"model": f"{MODEL_PREFIXES[model]}-{mode}", "input": inputs}
