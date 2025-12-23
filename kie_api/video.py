"""Video helpers shared across KIE models."""

from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

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


def _write_video_to_temp_file(video_bytes: bytes, suffix: str = ".mp4") -> str:
    """Persist video bytes to a temporary file and return its path."""
    try:
        temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
        with temp_file:
            temp_file.write(video_bytes)
        return str(Path(temp_file.name))
    except OSError as exc:
        raise RuntimeError("Failed to write temporary video file.") from exc


def _video_bytes_to_comfy_video(video_bytes: bytes):
    """Convert raw video bytes into a ComfyUI VIDEO object."""
    try:
        from comfy_api.latest.input_impl.video_types import VideoFromFile
    except ImportError as exc:
        raise RuntimeError(
            "comfy_api video helpers are unavailable. Update ComfyUI to a version that "
            "ships comfy_api.latest.input_impl.video_types."
        ) from exc

    buffer = BytesIO(video_bytes)
    buffer.name = "kie_temp_video.mp4"
    return VideoFromFile(buffer)
