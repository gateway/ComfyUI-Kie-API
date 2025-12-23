# kie_api/video.py

import os
import time

import folder_paths

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
    """Convert raw MP4 bytes into a classic ComfyUI VIDEO dict."""
    output_dir = folder_paths.get_output_directory()
    filename = f"kie_video_{time.time_ns()}.mp4"
    video_path = os.path.join(output_dir, filename)

    with open(video_path, "wb") as handle:
        handle.write(video_bytes)

    return {
        "filename": filename,
        "subfolder": "",
        "type": "output",
    }
