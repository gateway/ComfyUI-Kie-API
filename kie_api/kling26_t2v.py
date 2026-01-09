"""Kling 2.6 text-to-video helper."""

import time

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _poll_task_until_complete
from .kling26_i2v import _create_kling_task
from .log import _log
from .results import _extract_result_urls
from .validation import _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


MODEL_NAME = "kling-2.6/text-to-video"
PROMPT_MAX_LENGTH = 2500
ASPECT_RATIO_OPTIONS = ["1:1", "16:9", "9:16"]
DURATION_OPTIONS = ["5", "10"]


def run_kling26_t2v_video(
    prompt: str,
    sound: bool,
    aspect_ratio: str,
    duration: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> dict:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if duration not in DURATION_OPTIONS:
        raise RuntimeError("Invalid duration. Use the pinned enum options.")
    if not isinstance(sound, bool):
        raise RuntimeError("sound must be a boolean value.")

    api_key = _load_api_key()

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "sound": sound,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
        },
    }

    _log(log, "Creating Kling 2.6 T2V task...")
    start_time = time.time()
    task_id, create_response_text = _create_kling_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
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


def run_kling26_t2v(
    prompt: str,
    sound: bool = False,
    aspect_ratio: str = "9:16",
    duration: str = "5",
    poll_interval_s: float = 10.0,
    timeout_s: int = 1000,
    log: bool = True,
) -> dict:
    """Backward-compatible alias for existing imports."""
    return run_kling26_t2v_video(
        prompt=prompt,
        sound=sound,
        aspect_ratio=aspect_ratio,
        duration=duration,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
