"""Shared helpers for handling video results from KIE models."""

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
    """Persist video bytes to a temporary .mp4 file and return its path."""
    try:
        temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
        with temp_file:
            temp_file.write(video_bytes)
        return str(Path(temp_file.name))
    except OSError as exc:
        raise RuntimeError("Failed to write temporary video file.") from exc


def _video_path_to_comfy_video_output(video_path: str) -> dict:
    """Wrap a local video path in a ComfyUI VIDEO-compatible dict."""
    path = Path(video_path)
    suffix = path.suffix.lstrip(".") or "mp4"
    resolved = path.expanduser().resolve()
    return {
        "path": str(resolved),
        "format": suffix,
        "frame_rate": None,
        "frame_count": None,
    }
