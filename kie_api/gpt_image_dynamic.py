"""Native DynamicCombo schema and request translation; no runtime dependencies."""

from .gpt_image_options import (
    MODEL_OPTIONS, QUALITY_OPTIONS, SVG_MODELS, build_gpt_image_payload,
    model_widget_options,
)


def _guide_input(io, allow_mask):
    choices = [io.DynamicCombo.Option("None", [])]
    if allow_mask:
        choices.append(io.DynamicCombo.Option("Mask", [
            io.Mask.Input("mask", tooltip="One mask matching the first image; 1 = edit, 0 = preserve."),
        ]))
    choices.append(io.DynamicCombo.Option("Markup", [
        io.Image.Input("markup", tooltip="Separate RGB annotation layer, matching the first image."),
        io.Mask.Input("markup_mask", tooltip="Annotation transparency, 1 = transparent. Use Load Image's MASK output."),
    ]))
    return io.DynamicCombo.Input("edit_guide", options=choices, display_name="edit guide")


def _static_inputs(io, rules):
    return [io.DynamicCombo.Input("aspect", display_name="aspect ratio", options=[
        io.DynamicCombo.Option(ratio, [] if rules["economy"] else [
            io.Combo.Input("resolution", options=rules["resolutions"][ratio], default="1K"),
        ]) for ratio in rules["aspect_ratios"]
    ])]


def model_input(io, mode):
    """Let ComfyUI own branch visibility, serialization, and nested input sockets."""
    models = []
    for model in MODEL_OPTIONS:
        rules = model_widget_options(mode)[model]
        advanced = rules["advanced"]
        image_formats = [fmt for fmt in rules["formats"] if fmt not in ("gif", "svg")]
        image_fields = _static_inputs(io, rules) + [
            io.DynamicCombo.Input("format", display_name="image format", options=[
                io.DynamicCombo.Option(fmt, [
                    io.Combo.Input("background", options=["opaque"] if fmt == "jpeg" else rules["backgrounds"], default="opaque"),
                    *([io.Int.Input("output_compression", default=100, min=0, max=100)]
                      if advanced and fmt in ("jpeg", "webp") else []),
                ]) for fmt in image_formats
            ]),
        ]
        if advanced and mode == "image-to-image":
            image_fields.append(_guide_input(io, allow_mask=True))
        outputs = [io.DynamicCombo.Option("Image", image_fields)]
        if "svg" in rules["formats"]:
            fields = _static_inputs(io, rules) + [
                io.Combo.Input("background", options=rules["backgrounds"], default="opaque"),
                io.Combo.Input("svg_model", options=SVG_MODELS, default=SVG_MODELS[0]),
            ]
            if mode == "image-to-image":
                fields.append(_guide_input(io, allow_mask=False))
            outputs.append(io.DynamicCombo.Option("SVG", fields))
        if "gif" in rules["formats"]:
            fields = _static_inputs(io, rules) if rules["economy"] else []
            fields += [
                io.Combo.Input("background", options=rules["backgrounds"], default="opaque"),
                io.Combo.Input("frame_count", options=rules["frame_counts"], default="9"),
                io.Int.Input("frame_duration_ms", default=200, min=20, max=2000, step=10),
            ]
            if advanced and mode == "text-to-image":
                fields.append(io.String.Input("gif_size", default="auto", tooltip="Per-frame pixels: auto or e.g. 512x512."))
            if advanced and mode == "image-to-image":
                fields.append(_guide_input(io, allow_mask=False))
            outputs.append(io.DynamicCombo.Option("GIF", fields))
        fields = [io.DynamicCombo.Input("output", display_name="output mode", options=outputs)]
        if advanced:
            fields += [
                io.Combo.Input("quality", options=QUALITY_OPTIONS, default="medium"),
                io.Combo.Input("complexity", options=["high", "medium", "low"], default="high"),
                io.Combo.Input("moderation", options=["low", "auto"], default="low"),
            ]
        models.append(io.DynamicCombo.Option(model, fields))
    return io.DynamicCombo.Input("model", options=models)


def _group(value, name):
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} must be a native DynamicCombo selection.")
    return value


def request_options(prompt, model, mode):
    """Translate active native branches into the existing, validated helper inputs."""
    selection = _group(model, "model")
    model_name = selection.get("model")
    rules = model_widget_options(mode).get(model_name)
    if rules is None:
        raise RuntimeError("Choose a supported GPT Image model.")
    output = _group(selection.get("output"), "output")
    kind = output.get("output")
    if kind not in ("Image", "SVG", "GIF"):
        raise RuntimeError("Choose Image, SVG, or GIF output mode.")
    image_format = _group(output.get("format"), "image format") if kind == "Image" else {}
    fmt = image_format.get("format") if kind == "Image" else kind.lower()
    if kind == "Image" and fmt not in ("png", "jpeg", "webp"):
        raise RuntimeError("Image mode requires PNG, JPEG, or WebP.")
    aspect = _group(output.get("aspect"), "aspect ratio") if kind != "GIF" or rules["economy"] else {}
    args = dict(model=model_name, aspect_ratio=aspect.get("aspect", "auto"),
                resolution=aspect.get("resolution", "1K"), output_format=fmt,
                background=(image_format if kind == "Image" else output).get("background", "opaque"))
    if rules["advanced"]:
        for name, default in (("quality", "medium"), ("complexity", "high"), ("moderation", "low")):
            args[name] = selection.get(name, default)
    if fmt in ("jpeg", "webp"):
        args["output_compression"] = image_format.get("output_compression", 100)
    elif fmt == "svg":
        args["svg_model"] = output.get("svg_model", SVG_MODELS[0])
    elif fmt == "gif":
        args.update(frame_count=output.get("frame_count", "9"), frame_duration_ms=output.get("frame_duration_ms", 200))
        if rules["advanced"] and mode == "text-to-image":
            args["gif_size"] = output.get("gif_size", "auto")
    # Check variant, mode, format and value ranges before accessing any media.
    build_gpt_image_payload(prompt=prompt, mode=mode, **args)
    guide = _group(output.get("edit_guide", {"edit_guide": "None"}), "edit guide")
    guide_kind = guide.get("edit_guide")
    if guide_kind not in ("None", "Mask", "Markup"):
        raise RuntimeError("Choose None, Mask, or Markup for edit guide.")
    if guide_kind != "None":
        if mode != "image-to-image" or not rules["advanced"]:
            raise RuntimeError("Edit guides require 2.6 Flare/Sunburst image-to-image.")
        if guide_kind == "Mask" and kind != "Image":
            raise RuntimeError("Masks require Image output mode.")
        names = ("mask",) if guide_kind == "Mask" else ("markup", "markup_mask")
        for name in names:
            if guide.get(name) is None:
                raise RuntimeError(f"Connect {name} for {guide_kind} editing.")
            args[name] = guide[name]
    return args
