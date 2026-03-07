"""Grok Imagine text-to-image helper."""

import time

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .images import _download_images_as_batch
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .validation import _validate_prompt


MODEL_NAME = "grok-imagine/text-to-image"
PROMPT_MAX_LENGTH = 5000
ASPECT_RATIO_OPTIONS = ["2:3", "3:2", "1:1", "9:16", "16:9"]


def run_grok_imagine_t2i(
    prompt: str,
    aspect_ratio: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> tuple[torch.Tensor, str]:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")

    api_key = _load_api_key()
    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        },
    }

    _log(log, "Creating Grok Imagine T2I task...")
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
    _log(log, f"Result URLs: {result_urls}")
    _log(log, f"Downloading {len(result_urls)} Grok Imagine T2I result image(s)...")
    image_batch = _download_images_as_batch(result_urls)
    _log(log, "Images downloaded and decoded.")

    _log_remaining_credits(log, record_data, api_key, _log)
    return image_batch, task_id
