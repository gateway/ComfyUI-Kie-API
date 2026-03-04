"""Grok Imagine text-to-video helper."""

import time

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .validation import _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "grok-imagine/text-to-video"
PROMPT_MAX_LENGTH = 5000
ASPECT_RATIO_OPTIONS = ["16:9", "9:16", "1:1", "2:3", "3:2"]
MODE_OPTIONS = ["normal", "fun", "spicy"]
DURATION_OPTIONS = ["6", "10", "15"]
RESOLUTION_OPTIONS = ["480p", "720p"]


def run_grok_imagine_t2v_video(
    prompt: str,
    aspect_ratio: str,
    mode: str,
    duration: str,
    resolution: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> dict:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if mode not in MODE_OPTIONS:
        raise RuntimeError("Invalid mode. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if resolution not in RESOLUTION_OPTIONS:
        raise RuntimeError("Invalid resolution. Use the pinned enum options.")

    api_key = _load_api_key()

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "duration": duration,
            "resolution": resolution,
        },
    }

    _log(log, "Creating Grok Imagine T2V task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(
        log,
        f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}",
    )
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    result_urls = _extract_result_urls(record_data)
    video_url = result_urls[0]
    _log(log, f"Final video URL: {video_url}")

    video_bytes = _download_video(video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output
