# kie_api/video.py

import time
from pathlib import Path

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
    output_dir = folder_paths.get_output_directory()
    filename = f"kie_video_{int(time.time())}.mp4"
    path = Path(output_dir) / filename

    with open(path, "wb") as handle:
        handle.write(video_bytes)

    return folder_paths.VideoFile(
        filename=filename,
        subfolder="",
        type="output",
    )
