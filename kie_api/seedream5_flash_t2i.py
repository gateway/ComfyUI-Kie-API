"""Seedream 5.0 Flash text-to-image helper.

Implements the Seedream 5.0 Flash text-to-image endpoint documented at
https://docs.kie.ai/market/seedream/5-flash-text-to-image

Model id: `seedream/5-flash-text-to-image`.

Flash differences versus Pro/Lite: quality is expressed as a resolution tier in
the `size` field (`1K` / `1.5K` / `2K`) instead of the `quality` enum, and it is
the fast/cheap tier of the family.
"""

import json
import time
from typing import Any

import torch

from .auth import _load_api_key
from .http import TransientKieError, requests
from .images import _download_image, _image_bytes_to_tensor
from .jobs import _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .validation import _validate_prompt


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
MODEL_NAME = "seedream/5-flash-text-to-image"
ASPECT_RATIO_OPTIONS = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"]
# Flash expresses resolution as a tier instead of the Pro/Lite `quality` enum.
SIZE_OPTIONS = ["1K", "1.5K", "2K"]
OUTPUT_FORMAT_OPTIONS = ["png", "jpeg"]
PROMPT_MAX_LENGTH = 3000


def _validate_options(aspect_ratio: str, size: str, output_format: str) -> None:
    if aspect_ratio not in ASPECT_RATIO_OPTIONS:
        raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
    if size not in SIZE_OPTIONS:
        raise RuntimeError("Invalid size. Use the pinned enum options.")
    if output_format not in OUTPUT_FORMAT_OPTIONS:
        raise RuntimeError("Invalid output_format. Use the pinned enum options.")


def _create_seedream_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    try:
        response = requests.post(
            CREATE_TASK_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call createTask endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"createTask returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("createTask endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("message") or payload_json.get("msg")
        raise RuntimeError(f"createTask endpoint returned error code {payload_json.get('code')}: {message}")

    task_id = (payload_json.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError("createTask endpoint did not return a taskId.")

    return task_id, response.text


def run_seedream5_flash_text_to_image(
    prompt: str,
    aspect_ratio: str,
    size: str,
    output_format: str,
    nsfw_checker: bool,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> torch.Tensor:
    _validate_prompt(prompt, max_length=PROMPT_MAX_LENGTH)
    _validate_options(aspect_ratio, size, output_format)

    api_key = _load_api_key()
    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "size": size,
            "output_format": output_format,
            "nsfw_checker": nsfw_checker,
        },
    }

    _log(log, "Creating Seedream 5.0 Flash text-to-image task...")
    start_time = time.time()
    task_id, create_response_text = _create_seedream_task(api_key, payload)
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
    _log(log, f"Result URLs: {result_urls}")
    _log(log, f"Downloading result image from {result_urls[0]}...")

    image_bytes = _download_image(result_urls[0])
    image_tensor = _image_bytes_to_tensor(image_bytes)
    _log(log, "Image downloaded and decoded.")

    return image_tensor
