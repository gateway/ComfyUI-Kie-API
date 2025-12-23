"""Video helpers shared across KIE models."""

from io import BytesIO

from comfy_api.latest.input_impl.video_types import VideoFromFile

from .http import requests


def _download_video(url: str) -> bytes:
    """Download video bytes from a result URL."""
    try:
        response = requests.get(url, timeout=180)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download result video: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download result video (status code {response.status_code}).")

    return response.content


def _video_bytes_to_comfy_video(video_bytes: bytes) -> VideoFromFile:
    """Convert raw MP4 bytes into a ComfyUI VIDEO object."""
    buffer = BytesIO(video_bytes)
    buffer.name = "kie_temp_video.mp4"
    return VideoFromFile(buffer)
