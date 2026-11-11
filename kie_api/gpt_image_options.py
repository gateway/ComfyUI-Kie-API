"""Pinned Kie GPT Image contracts shared by validation and widget metadata."""

DEFAULT_MODEL = "GPT Image 2"
MODEL_PREFIXES = {
    DEFAULT_MODEL: "gpt-image-2",
    "GPT Image 2.5 Flare": "gpt-image-2-5-flare",
    "GPT Image 2.5 Sunburst": "gpt-image-2-5-sunburst",
    "GPT Image 2.6 Flare": "gpt-image-2-6/flare",
    "GPT Image 2.6 Sunburst": "gpt-image-2-6/sunburst",
    "GPT Image 2.6 Economy": "gpt-image-2-6/economy",
}
MODEL_OPTIONS = list(MODEL_PREFIXES)
LEGACY_ASPECT_RATIOS = ["auto", "1:1", "9:16", "16:9", "4:3", "3:4"]
V25_RATIOS = [*LEGACY_ASPECT_RATIOS, "3:2", "2:3", "21:9", "27:16", "16:27", "9:8", "8:9"]
V26_RATIOS = ["auto", "1:1", "3:2", "2:3", "4:3", "3:4", "5:4", "4:5", "16:9", "9:16", "2:1", "1:2", "21:9", "9:21", "3:1", "1:3"]
ECONOMY_RATIOS = ["auto", "1:1", "16:9", "9:16", "3:2", "2:3", "21:9", "4:3"]
ASPECT_RATIO_OPTIONS = list(dict.fromkeys(V25_RATIOS + V26_RATIOS))
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
BACKGROUND_OPTIONS = ["opaque", "transparent", "auto"]
QUALITY_OPTIONS = ["medium", "low", "high", "xhigh", "max", "auto"]
FORMAT_OPTIONS = ["png", "jpeg", "webp", "gif", "svg"]
SVG_MODELS = ["gpt-5.6-luna", "gpt-6-sol", "gpt-5.6-terra"]
ONE_K_ONLY_RATIOS = {"27:16", "16:27", "9:8", "8:9"}
PROMPT_MAX_LENGTH = 20000
MAX_IMAGE_COUNT = 16


def model_widget_options(mode="text-to-image") -> dict:
    options = {}
    for model in MODEL_OPTIONS:
        legacy = model == DEFAULT_MODEL
        modern = model.startswith("GPT Image 2.6")
        economy = model.endswith("Economy")
        ratios = ECONOMY_RATIOS if economy else V26_RATIOS if modern else LEGACY_ASPECT_RATIOS if legacy else V25_RATIOS
        resolutions = {}
        for ratio in ratios:
            if economy or (legacy and ratio == "auto") or (not modern and ratio in ONE_K_ONLY_RATIOS):
                resolutions[ratio] = ["1K"]
            elif legacy and ratio == "1:1":
                resolutions[ratio] = ["1K", "2K"]
            else:
                resolutions[ratio] = list(RESOLUTION_OPTIONS)
        formats = (["png", "gif"] if mode == "text-to-image" else ["png"]) if economy else FORMAT_OPTIONS if modern else ["png"]
        options[model] = {
            "aspect_ratios": list(ratios), "resolutions": resolutions,
            "backgrounds": ["opaque"] if legacy else list(BACKGROUND_OPTIONS),
            "formats": list(formats), "advanced": modern and not economy,
            "economy": economy,
            "frame_counts": ["auto", "4", "9", "16", "25", "36", "64"] if economy else [str(n) for n in range(2, 17)],
        }
    return options


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be an integer from {minimum} to {maximum}.")
    return value


def build_gpt_image_payload(
    *, model: str, mode: str, prompt: str, aspect_ratio: str,
    resolution: str, background: str, output_format="png", quality="medium",
    complexity="high", moderation="low", output_compression=100,
    frame_count="9", frame_duration_ms=200, gif_size="auto", svg_model="gpt-5.6-luna",
) -> dict:
    """Only active controls are serialized; inactive widget values are ignored."""
    if model not in MODEL_PREFIXES:
        raise RuntimeError(f"Unknown GPT Image model: {model!r}.")
    if mode not in ("text-to-image", "image-to-image"):
        raise RuntimeError(f"Unknown GPT Image mode: {mode!r}.")
    options = model_widget_options(mode)[model]
    if not isinstance(prompt, str) or not prompt.strip():
        raise RuntimeError("Prompt is required.")
    limit = 32000 if options["advanced"] else PROMPT_MAX_LENGTH
    if len(prompt) > limit:
        raise RuntimeError(f"Prompt exceeds the maximum length of {limit} characters.")
    if output_format not in options["formats"]:
        raise RuntimeError(f"{model} {mode} supports output formats: {', '.join(options['formats'])}.")
    if background not in options["backgrounds"]:
        raise RuntimeError(f"{model} supports background: {', '.join(options['backgrounds'])}.")
    inputs = {"prompt": prompt}
    # Standard GIF uses per-frame size, not the static resolution table.
    if output_format != "gif" or options["economy"]:
        if aspect_ratio not in options["aspect_ratios"]:
            raise RuntimeError(f"{model} does not support aspect_ratio {aspect_ratio!r}.")
        if resolution not in options["resolutions"][aspect_ratio]:
            raise RuntimeError(f"{model} with aspect_ratio {aspect_ratio!r} does not support {resolution}.")
        inputs["aspect_ratio"] = aspect_ratio
        if not options["economy"]:
            inputs["resolution"] = resolution
    if model != DEFAULT_MODEL:
        inputs["background"] = background
    if model.startswith("GPT Image 2.6"):
        inputs["output_format"] = output_format
    if options["advanced"]:
        for name, value, allowed in (("quality", quality, QUALITY_OPTIONS), ("complexity", complexity, ["low", "medium", "high"]), ("moderation", moderation, ["auto", "low"])):
            if value not in allowed:
                raise RuntimeError(f"Invalid {name}: {value!r}.")
            inputs[name] = value
        if background == "transparent" and output_format == "jpeg":
            raise RuntimeError("JPEG cannot preserve transparency; choose PNG or WebP.")
        if output_format in ("jpeg", "webp"):
            inputs["output_compression"] = _integer(output_compression, "output_compression", 0, 100)
        if output_format == "svg":
            if svg_model not in SVG_MODELS:
                raise RuntimeError("Unknown SVG author model.")
            inputs["svg"] = {"model": svg_model}
    if output_format == "gif":
        count = str(frame_count)
        if count not in options["frame_counts"]:
            raise RuntimeError(f"frame_count must be one of {options['frame_counts']}.")
        inputs["frame_count"] = count if options["economy"] else int(count)
        duration = _integer(frame_duration_ms, "frame_duration_ms", 20, 2000)
        if duration % 10:
            raise RuntimeError("frame_duration_ms must be a multiple of 10.")
        inputs["frame_duration_ms"] = duration
        if options["advanced"] and mode == "text-to-image":
            validate_gif_size(gif_size, int(count))
            inputs["size"] = gif_size
    return {"model": f"{MODEL_PREFIXES[model]}-{mode}", "input": inputs}


def validate_gif_size(size, count):
    if size == "auto":
        return
    try:
        width, height = map(int, size.split("x"))
    except (ValueError, AttributeError):
        raise RuntimeError("GIF size must be auto or WIDTHxHEIGHT, e.g. 512x512.") from None
    if min(width, height) <= 0 or width % 16 or height % 16:
        raise RuntimeError("GIF frame dimensions must be positive multiples of 16.")
    cols, rows = (4, 2) if count <= 8 else (3, 3) if count == 9 else (4, 3) if count <= 12 else (4, 4)
    for c, r in ((cols, rows), (rows, cols)):
        w, h = width * c, height * r
        if max(w, h) <= 3840 and w * h <= 8294400 and max(w, h) <= 3 * min(w, h):
            return
    raise RuntimeError("GIF sprite sheet exceeds provider limits; reduce frame size or count.")


def generation_widgets():
    """Append after legacy widgets to preserve saved workflow ordering."""
    return {
        "output_format": (FORMAT_OPTIONS, {"default": "png"}),
        "quality": (QUALITY_OPTIONS, {"default": "medium"}),
        "complexity": (["high", "medium", "low"], {"default": "high"}),
        "moderation": (["low", "auto"], {"default": "low"}),
        "output_compression": ("INT", {"default": 100, "min": 0, "max": 100}),
        "frame_count": (["9", "auto", *[str(n) for n in range(2, 17) if n != 9], "25", "36", "64"], {"default": "9"}),
        "frame_duration_ms": ("INT", {"default": 200, "min": 20, "max": 2000, "step": 10}),
        "gif_size": ("STRING", {"default": "auto", "tooltip": "2.6 Flare/Sunburst T2I GIF only: auto or frame pixels, e.g. 512x512."}),
        "svg_model": (SVG_MODELS, {"default": SVG_MODELS[0]}),
    }
