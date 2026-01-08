import json
from io import BytesIO
from typing import Any

import torch
from PIL import Image

from .http import TransientKieError, requests


UPLOAD_URL = "https://kieai.redpandaai.co/api/file-stream-upload"
UPLOAD_PATH = "images/user-uploads"


def _truncate_url(url: str, max_length: int = 80) -> str:
    if len(url) <= max_length:
        return url
    return url[:max_length] + "..."


def _image_tensor_to_png_bytes(image: torch.Tensor) -> bytes:
    if image.dim() != 3 or image.shape[2] != 3:
        raise RuntimeError("Image tensor must have shape [H, W, 3].")
    if image.numel() == 0:
        raise RuntimeError("Image tensor is empty.")

    if image.dtype != torch.uint8:
        working = image.detach().cpu().clamp(0, 1) * 255.0
        working = working.round().to(torch.uint8)
    else:
        working = image.detach().cpu()

    working = working.contiguous()
    height, width, _channels = working.shape
    data_bytes = bytes(working.view(-1).tolist())

    try:
        pil_image = Image.frombytes("RGB", (width, height), data_bytes)
    except Exception as exc:
        raise RuntimeError("Failed to convert tensor to image.") from exc

    with BytesIO() as output:
        pil_image.save(output, format="PNG")
        return output.getvalue()


def _upload_image(api_key: str, png_bytes: bytes) -> str:
    try:
        response = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("image.png", png_bytes, "image/png")},
            data={"uploadPath": UPLOAD_PATH},
            timeout=120,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to upload image: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"upload returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Upload endpoint did not return valid JSON.") from exc

    success = payload_json.get("success")
    code = payload_json.get("code")
    if not success or code != 200:
        raise RuntimeError(f"Upload failed (code={code}): {payload_json.get('msg')}")

    data = payload_json.get("data") or {}
    url = data.get("downloadUrl")
    if not url:
        raise RuntimeError("Upload response missing downloadUrl.")

    return url


def _upload_video(api_key: str, video_bytes: bytes, filename: str = "video.mp4") -> str:
    if not filename:
        raise RuntimeError("filename is required for video uploads.")
    try:
        response = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, video_bytes, "video/mp4")},
            data={"uploadPath": UPLOAD_PATH, "fileName": filename},
            timeout=180,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to upload video: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"upload returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Upload endpoint did not return valid JSON.") from exc

    success = payload_json.get("success")
    code = payload_json.get("code")
    if not success or code != 200:
        raise RuntimeError(f"Upload failed (code={code}): {payload_json.get('msg')}")

    data = payload_json.get("data") or {}
    url = data.get("downloadUrl")
    if not url:
        raise RuntimeError("Upload response missing downloadUrl.")

    return url
