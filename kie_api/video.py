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


def _coerce_video_to_mp4_bytes(video) -> tuple[bytes, str]:
    """Coerce ComfyUI VIDEO input into MP4 bytes for upload."""
    if isinstance(video, (bytes, bytearray)):
        return bytes(video), "bytes"

    if isinstance(video, str):
        try:
            return Path(video).read_bytes(), f"path:{video}"
        except OSError as exc:
            raise RuntimeError(f"Failed to read video file: {exc}") from exc

    if isinstance(video, dict):
        video_path = video.get("path") or video.get("filename")
        if not video_path:
            raise RuntimeError("video input dict must include a 'path' or 'filename'.")
        try:
            return Path(video_path).read_bytes(), f"dict_path:{video_path}"
        except OSError as exc:
            raise RuntimeError(f"Failed to read video file: {exc}") from exc

    temp_dir = None
    for attr in ("get_temp_directory", "get_temp_folder", "get_output_directory"):
        getter = getattr(folder_paths, attr, None)
        if callable(getter):
            temp_dir = Path(getter())
            break
    if temp_dir is None:
        temp_dir = Path.cwd()

    if hasattr(video, "save_to") and callable(getattr(video, "save_to")):
        temp_path = temp_dir / f"kie_video_{int(time.time() * 1000)}.mp4"
        try:
            video.save_to(str(temp_path))
            return temp_path.read_bytes(), f"save_to:{temp_path}"
        except Exception as exc:
            raise RuntimeError(f"Failed to save Comfy VIDEO input: {exc}") from exc

    if hasattr(video, "save") and callable(getattr(video, "save")):
        temp_path = temp_dir / f"kie_video_{int(time.time() * 1000)}.mp4"
        try:
            video.save(str(temp_path))
            return temp_path.read_bytes(), f"save:{temp_path}"
        except Exception as exc:
            raise RuntimeError(f"Failed to save Comfy VIDEO input: {exc}") from exc

    path_attr = getattr(video, "path", None)
    if isinstance(path_attr, str):
        try:
            return Path(path_attr).read_bytes(), f"path_attr:{path_attr}"
        except OSError as exc:
            raise RuntimeError(f"Failed to read video file: {exc}") from exc

    raise RuntimeError("video input must be bytes, a file path string, a dict with a path, or a Comfy VIDEO object.")


def _video_bytes_to_comfy_video(video_bytes: bytes):
    """
    Convert MP4 bytes into a ComfyUI VIDEO object that the official SaveVideo node accepts.
    """
    buf = BytesIO(video_bytes)
    buf.seek(0)
    return InputImpl.VideoFromFile(buf)
