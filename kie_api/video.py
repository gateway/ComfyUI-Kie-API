# kie_api/video.py

from io import BytesIO
from typing import Any

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
    Convert raw MP4 bytes into a ComfyUI VIDEO object.
    This is what SaveVideo expects.
    """
    # Import inside function to avoid Comfy startup import issues
    from comfy_api.latest.input_impl.video_types import VideoFromFile

    return VideoFromFile(BytesIO(video_bytes))
