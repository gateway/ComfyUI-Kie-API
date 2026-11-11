"""Alpha edit guides and lossless output handling for the GPT Image nodes."""

from io import BytesIO
import json
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageSequence
import torch


def _mask_plane(mask, height, width, name):
    if not isinstance(mask, torch.Tensor):
        raise RuntimeError(f"{name} must be a ComfyUI MASK tensor.")
    if mask.ndim == 2:
        mask = mask.unsqueeze(0)
    if tuple(mask.shape) != (1, height, width):
        raise RuntimeError(f"{name} must contain exactly one mask matching the first image ({width}x{height}).")
    if not torch.isfinite(mask).all() or (mask < 0).any() or (mask > 1).any():
        raise RuntimeError(f"{name} must contain finite values between 0 and 1.")
    return mask[0].detach().cpu().float().numpy()


def prepare_edit_guide(*, images, model, output_format, mask=None, markup=None, markup_mask=None):
    """Return a provider field and encoded PNG, validating before auth/uploads."""
    if mask is not None and (markup is not None or markup_mask is not None):
        raise RuntimeError("Connect either mask or markup, never both.")
    if mask is None and markup is None and markup_mask is None:
        return None
    if model not in ("GPT Image 2.6 Flare", "GPT Image 2.6 Sunburst"):
        raise RuntimeError("Mask and markup editing require GPT Image 2.6 Flare or Sunburst.")
    height, width = images.shape[1:3]
    if mask is not None:
        if output_format in ("gif", "svg"):
            raise RuntimeError("Masks cannot be used with GIF or SVG output.")
        alpha = 1.0 - _mask_plane(mask, height, width, "mask")
        rgba = np.ones((height, width, 4), dtype=np.float32)
        rgba[:, :, 3] = alpha
        field = "mask_url"
    else:
        if not isinstance(markup, torch.Tensor) or markup.ndim != 4 or markup.shape[0] != 1 or tuple(markup.shape[1:3]) != (height, width) or markup.shape[3] not in (3, 4):
            raise RuntimeError("markup must be one RGB/RGBA IMAGE matching the first source image dimensions.")
        if not torch.isfinite(markup).all() or (markup < 0).any() or (markup > 1).any():
            raise RuntimeError("markup must contain finite values between 0 and 1.")
        pixels = markup[0].detach().cpu().float().numpy()
        if markup.shape[3] == 4:
            if markup_mask is not None:
                raise RuntimeError("RGBA markup already has alpha; disconnect markup_mask.")
            rgba = pixels.copy()
        else:
            if markup_mask is None:
                raise RuntimeError("RGB markup requires markup_mask (1 = transparent). Connect both outputs of Load Image for an annotation PNG.")
            alpha = 1.0 - _mask_plane(markup_mask, height, width, "markup_mask")
            rgba = np.concatenate((pixels, alpha[:, :, None]), axis=2)
        if not (rgba[:, :, 3] < 1).any() or not (rgba[:, :, 3] > 0).any():
            raise RuntimeError("Markup must contain visible annotations and transparent pixels; do not flatten it onto the source image.")
        field = "markup"
    output = BytesIO()
    Image.fromarray(np.round(rgba * 255).astype(np.uint8), "RGBA").save(output, format="PNG")
    data = output.getvalue()
    if len(data) >= 30 * 1024 * 1024:
        raise RuntimeError("Edit guide PNG exceeds Kie's 30 MB upload limit.")
    return field, data


def decode_result(data, expected_format):
    """Decode native output; SVG has no fabricated raster preview."""
    if expected_format == "svg":
        try:
            text = data.decode("utf-8-sig")
            if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
                raise ValueError("XML declarations with entities are not supported")
            root = ET.fromstring(text)
            if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
                raise ValueError("not an SVG root")
        except (UnicodeError, ET.ParseError, ValueError) as exc:
            raise RuntimeError("Provider did not return a valid UTF-8 SVG document.") from exc
        return None, None, text, {"format": "svg", "mime_type": "image/svg+xml"}
    frames, masks, durations = [], [], []
    try:
        with Image.open(BytesIO(data)) as source:
            actual = (source.format or "").lower()
            if actual not in ("png", "jpeg", "webp", "gif"):
                raise RuntimeError(f"Unsupported provider output format: {actual}.")
            if expected_format is not None and actual != expected_format:
                raise RuntimeError(f"Requested {expected_format}, but provider returned {actual}.")
            loop = source.info.get("loop")
            for frame in ImageSequence.Iterator(source):
                rgba = np.array(frame.convert("RGBA"), dtype=np.float32) / 255.0
                frames.append(torch.from_numpy(rgba[:, :, :3].copy()))
                masks.append(torch.from_numpy(1.0 - rgba[:, :, 3]))
                durations.append(frame.info.get("duration", 0))
            metadata = {"format": actual, "mime_type": f"image/{actual}",
                        "width": source.width, "height": source.height,
                        "frame_count": len(frames)}
            if actual == "gif":
                metadata.update(frame_durations_ms=durations, loop=loop)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Failed to decode provider image output.") from exc
    return torch.stack(frames), torch.stack(masks), "", metadata


def collect_results(downloads, *, task_id, output_format, output_dir):
    """Save every original; return IMAGE, MASK, paths JSON, SVG text, metadata JSON."""
    directory = Path(output_dir) / "kie_gpt_image"
    directory.mkdir(parents=True, exist_ok=True)
    batch, masks, paths, vectors, records = [], [], [], [], []
    prefix = uuid.uuid4().hex
    for index, (url, data) in enumerate(downloads):
        image, mask, svg, metadata = decode_result(data, output_format)
        path = directory / f"{prefix}_{index}.{metadata['format']}"
        path.write_bytes(data)
        paths.append(str(path.resolve()))
        records.append({**metadata, "path": paths[-1], "url": url, "bytes": len(data)})
        if image is not None:
            batch.append(image)
            masks.append(mask)
        if svg:
            vectors.append(svg)
    if not records:
        raise RuntimeError("Provider returned no output files.")
    if batch and any(item.shape[1:] != batch[0].shape[1:] for item in batch):
        raise RuntimeError(f"Output sizes differ and cannot form an IMAGE batch. Originals saved: {paths}")
    # Multiple vector documents remain separately recoverable without invalid XML concatenation.
    svg_text = vectors[0] if len(vectors) == 1 else json.dumps(vectors) if vectors else ""
    return (torch.cat(batch) if batch else None, torch.cat(masks) if masks else None,
            json.dumps(paths), svg_text, json.dumps({"task_id": task_id, "outputs": records}))
