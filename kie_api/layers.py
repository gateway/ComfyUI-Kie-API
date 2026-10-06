"""Shared layer-decomposition assembly for the Seedream 5.0 layer endpoints.

Used by `seedream5_flash_layer.py` (`seedream/5-flash-layer-decomposition`) and
`seedream5_pro_layer.py` (`seedream/5-pro-layer-decomposition`); both endpoints
take the same inputs and return the same payload shape, so the model id and the
allowed `size` tiers are the only differences.

The endpoint takes exactly ONE source image and returns a base image plus up to
16 transparent layers, each with its bounding box, stacking order and a
model-generated name/description.

The result is reassembled for ComfyUI as three aligned outputs so the layers can
be composited over one another:

- ``images``: IMAGE batch, one entry per returned image (base first, then layers
  in ascending z_index). Every entry is placed on a canvas the size of the base
  image at its bounding box position, so the batch is directly stackable.
- ``masks``: MASK batch with the same order/size, using the same inverse-alpha
  convention as the rest of the pack (1.0 = transparent, 0.0 = opaque).
- ``layer_info``: STRING, a JSON report (z_index, name, description, size,
  bounding_box, url) so the layer stack can be driven by hand or by another node.

Layer metadata is model-dependent: the Pro endpoint returns `layers_data` (names,
z_index, bounding boxes) and its result recomposes into the original, while the
Flash endpoint returns only `resultUrls` - full-canvas per-element plates with no
position metadata, which are handed over as-is.

Prompts are optional: without one the model picks the main elements itself.
``<bbox>x1 y1 x2 y2</bbox>`` (normalised 0-1000) can be used to target elements.

The credit cost and remaining balance of the task are logged by the shared poller
in `jobs.py`.
"""

import json
import time
from io import BytesIO
from typing import Any, Sequence

import numpy as np
import torch
from PIL import Image

from .auth import _load_api_key
from .images import _download_image
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch


OUTPUT_FORMAT_OPTIONS = ["png", "jpeg"]
PROMPT_MAX_LENGTH = 5000


def _validate_options(size: str, output_format: str, size_options: Sequence[str]) -> None:
    if size not in size_options:
        raise RuntimeError("Invalid size. Use the pinned enum options.")
    if output_format not in OUTPUT_FORMAT_OPTIONS:
        raise RuntimeError("Invalid output_format. Use the pinned enum options.")


def _parse_layers(record_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (layers_data sorted by z_index, result_urls)."""
    result_json = record_data.get("resultJson")
    if not result_json:
        raise RuntimeError("Task completed without resultJson.")
    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("resultJson is not valid JSON.") from exc

    result_urls = parsed.get("resultUrls") or []
    result_object = parsed.get("resultObject") or {}
    layers = result_object.get("layers_data") or []

    if layers:
        layers = sorted(layers, key=lambda item: item.get("z_index", 0))
    elif result_urls:
        # Fallback: no metadata, treat every URL as its own layer on a shared canvas.
        layers = [{"z_index": idx, "url": url, "name": f"layer_{idx}"} for idx, url in enumerate(result_urls)]
    else:
        raise RuntimeError("resultJson contains neither layers_data nor resultUrls.")

    return layers, result_urls


def _decode_rgba(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes to a float32 RGBA array in [0, 1]."""
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            return np.array(img.convert("RGBA"), dtype=np.float32) / 255.0
    except Exception as exc:
        raise RuntimeError("Failed to decode result image.") from exc


def _resize_rgba(rgba: np.ndarray, width: int, height: int) -> np.ndarray:
    if rgba.shape[1] == width and rgba.shape[0] == height:
        return rgba
    image = Image.fromarray((rgba * 255.0).round().astype(np.uint8), mode="RGBA")
    image = image.resize((width, height), Image.LANCZOS)
    return np.array(image, dtype=np.float32) / 255.0


def _parse_size(size_value: Any) -> tuple[int, int] | None:
    """Parse a metadata '1080x1080' size string into (width, height)."""
    if not isinstance(size_value, str) or "x" not in size_value:
        return None
    left, _, right = size_value.partition("x")
    try:
        return int(left), int(right)
    except ValueError:
        return None


def run_layer_decomposition(
    model_name: str,
    size_options: Sequence[str],
    image: torch.Tensor,
    prompt: str,
    size: str,
    output_format: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> tuple[torch.Tensor, torch.Tensor, str]:
    """Split one source image into a base image plus layers.

    Returns:
        (images, masks, layer_info): IMAGE batch, MASK batch (inverse alpha) and a
        JSON string describing the layer stack.
    """
    _validate_options(size, output_format, size_options)
    image = _validate_image_tensor_batch(image)
    if image.shape[0] > 1:
        _log(log, f"{image.shape[0]} images provided; layer decomposition uses only the first one.")

    prompt = (prompt or "").strip()
    if prompt and len(prompt) > PROMPT_MAX_LENGTH:
        raise RuntimeError(f"Prompt exceeds the maximum length of {PROMPT_MAX_LENGTH} characters.")

    api_key = _load_api_key()

    _log(log, "Uploading source image...")
    source_url = _upload_image(api_key, _image_tensor_to_png_bytes(image[0]))
    _log(log, f"Image upload success: {_truncate_url(source_url)}")

    input_payload: dict[str, Any] = {
        "image_url": source_url,
        "size": size,
        "output_format": output_format,
    }
    if prompt:
        input_payload["prompt"] = prompt

    payload = {"model": model_name, "input": input_payload}

    _log(log, f"Creating layer decomposition task ({model_name})...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(api_key, task_id, poll_interval_s, timeout_s, log, start_time)

    layers, result_urls = _parse_layers(record_data)
    _log(log, f"Task returned {len(layers)} image(s) ({len(result_urls)} URL(s) in resultUrls)")
    if not any(layer.get("bounding_box") for layer in layers):
        _log(
            log,
            "This model returned no layer metadata (no bounding boxes): every image is a full-canvas "
            "plate kept in URL order, because it cannot be positioned automatically.",
        )

    decoded: list[tuple[dict[str, Any], np.ndarray]] = []
    for idx, layer in enumerate(layers):
        url = layer.get("url")
        if not url:
            _log(log, f"Layer {idx} has no url; skipping.")
            continue
        _log(log, f"Downloading layer {idx + 1}/{len(layers)} (z_index={layer.get('z_index')}, name={layer.get('name')!r})")
        decoded.append((layer, _decode_rgba(_download_image(url))))

    if not decoded:
        raise RuntimeError("No layer images could be downloaded.")

    base_layer, base_rgba = decoded[0]
    canvas_height, canvas_width = base_rgba.shape[0], base_rgba.shape[1]
    _log(log, f"Base canvas: {canvas_width}x{canvas_height}")

    images: list[torch.Tensor] = []
    masks: list[torch.Tensor] = []
    report: list[dict[str, Any]] = []

    for position, (layer, rgba) in enumerate(decoded):
        canvas_rgb = np.zeros((canvas_height, canvas_width, 3), dtype=np.float32)
        canvas_alpha = np.zeros((canvas_height, canvas_width), dtype=np.float32)

        box = (layer.get("bounding_box") or {}).get("absolute")
        if position == 0 or not box:
            # Base image (or metadata-less fallback): fill the whole canvas.
            placed = _resize_rgba(rgba, canvas_width, canvas_height)
            canvas_rgb[:] = placed[:, :, :3]
            canvas_alpha[:] = placed[:, :, 3]
            origin = (0, 0)
            target_size = (canvas_width, canvas_height)
        else:
            left, top, right, bottom = (int(round(value)) for value in box[:4])
            parsed = _parse_size(layer.get("size"))
            width = right - left if right > left else (parsed[0] if parsed else rgba.shape[1])
            height = bottom - top if bottom > top else (parsed[1] if parsed else rgba.shape[0])
            placed = _resize_rgba(rgba, width, height)
            origin = (left, top)
            target_size = (width, height)

            src_left, src_top = max(0, -left), max(0, -top)
            dst_left, dst_top = max(0, left), max(0, top)
            pasted_width = min(width - src_left, canvas_width - dst_left)
            pasted_height = min(height - src_top, canvas_height - dst_top)
            if pasted_width > 0 and pasted_height > 0:
                canvas_rgb[dst_top : dst_top + pasted_height, dst_left : dst_left + pasted_width] = placed[
                    src_top : src_top + pasted_height, src_left : src_left + pasted_width, :3
                ]
                canvas_alpha[dst_top : dst_top + pasted_height, dst_left : dst_left + pasted_width] = placed[
                    src_top : src_top + pasted_height, src_left : src_left + pasted_width, 3
                ]

        images.append(torch.from_numpy(canvas_rgb.copy()).unsqueeze(0))
        # Same inverse-alpha convention as the rest of the pack: 1.0 = transparent.
        masks.append(torch.from_numpy((1.0 - canvas_alpha).copy()).unsqueeze(0))
        report.append(
            {
                "index": position,
                "z_index": layer.get("z_index"),
                "name": layer.get("name"),
                "description": layer.get("description"),
                "size": list(target_size),
                "origin": list(origin),
                "bounding_box": layer.get("bounding_box"),
                "url": layer.get("url"),
            }
        )
        _log(log, f"Layer {position}: {layer.get('name')!r} placed at {origin} size {target_size}")

    image_batch = torch.cat(images, dim=0)
    mask_batch = torch.cat(masks, dim=0)
    layer_info = json.dumps(report, indent=2, ensure_ascii=False)

    _log(log, f"Assembled IMAGE batch {tuple(image_batch.shape)} and MASK batch {tuple(mask_batch.shape)}")
    return image_batch, mask_batch, layer_info
