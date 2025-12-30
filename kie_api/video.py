# kie_api/video.py

import time
from io import BytesIO
from pathlib import Path

import folder_paths
from comfy_api.latest import InputImpl

from .http import requests


def _download_video(url: str) -> bytes:
    """Download video bytes from a result URL."""
    try:
        response = requests.get(url, timeout=180)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download result video: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download result video (status code {response.status_code})."
        )

    return response.content


def _video_bytes_to_comfy_video(video_bytes: bytes):
    """
    Convert MP4 bytes into a ComfyUI VIDEO object that the official SaveVideo node accepts.
    """
    buf = BytesIO(video_bytes)
    buf.seek(0)
    return InputImpl.VideoFromFile(buf)
