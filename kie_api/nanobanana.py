import json
import time
from io import BytesIO
from typing import Any

import torch
from PIL import Image

from .http import TransientKieError, requests


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
MODEL_NAME = "nano-banana-pro"
ASPECT_RATIO_OPTIONS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "auto"]
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
OUTPUT_FORMAT_OPTIONS = ["png", "jpg"]


def _log(enabled: bool, msg: str) -> None:
    if enabled:
        print(f"[KIE] {msg}")


def _validate_prompt(prompt: str) -> None:
    if not prompt:
        raise RuntimeError("Prompt is required.")
    if len(prompt) > 10000:
        raise RuntimeError("Prompt exceeds the maximum length of 10000 characters.")


def _create_nano_banana_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
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


def _fetch_task_record(api_key: str, task_id: str) -> tuple[dict[str, Any], str, Any]:
    try:
        response = requests.get(
            RECORD_INFO_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"taskId": task_id},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call recordInfo endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"recordInfo returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    raw_text = response.text
    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("recordInfo endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("message") or payload_json.get("msg")
        raise RuntimeError(f"recordInfo endpoint returned error code {payload_json.get('code')}: {message}")

    data = payload_json.get("data")
    if data is None:
        raise RuntimeError("recordInfo endpoint returned no data field.")

    return data, raw_text, payload_json.get("message") or payload_json.get("msg")


def _should_retry_fail(fail_code: Any, fail_msg: Any, message: Any) -> bool:
    try:
        code_int = int(fail_code)
    except (TypeError, ValueError):
        code_int = None

    if code_int is not None and 500 <= code_int <= 599:
        return True

    combined_text = " ".join(
        str(part).lower()
        for part in (fail_msg, message)
        if isinstance(part, str) and part
    )

    if "internal error" in combined_text or "try again later" in combined_text:
        return True

    return False


def _poll_task_until_complete(
    api_key: str,
    task_id: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
    start_time: float,
) -> tuple[dict[str, Any], str, Any, str | None]:
    interval = poll_interval_s if poll_interval_s > 0 else 1.0
    last_state = None
    last_log_time = start_time

    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed > timeout_s:
            last_state_text = last_state if last_state is not None else "unknown"
            raise RuntimeError(
                f"Task {task_id} timed out after {timeout_s}s (last state={last_state_text}, elapsed={elapsed:.1f}s). "
                "Try increasing timeout or retry."
            )

        data, raw_json, message_field = _fetch_task_record(api_key, task_id)
        state = data.get("state")
        should_log = log and (state != last_state or (now - last_log_time) >= 30.0)
        if should_log:
            _log(log, f"recordInfo response: {raw_json}")
            _log(log, f"Task {task_id} state: {state or 'unknown'} (elapsed={elapsed:.1f}s)")
            last_log_time = now

        last_state = state

        if state == "success":
            return data, raw_json, message_field, f"{elapsed:.1f}s"
        if state == "fail":
            fail_code = data.get("failCode")
            fail_msg = data.get("failMsg") or data.get("msg")
            parts = [f"Task {task_id} failed"]
            if fail_code is not None:
                parts.append(f"failCode={fail_code}")
            if fail_msg:
                parts.append(f"failMsg={fail_msg}")
            if message_field:
                parts.append(f"message={message_field}")
            error_message = "; ".join(parts)

            if _should_retry_fail(fail_code, fail_msg, message_field):
                raise TransientKieError(error_message)

            raise RuntimeError(error_message)

        if should_log:
            _log(log, f"Polling again in {interval} seconds...")
        time.sleep(interval)


def _extract_result_urls(record_data: dict[str, Any]) -> list[str]:
    result_json = record_data.get("resultJson")
    if not result_json:
        raise RuntimeError("Task completed without resultJson.")

    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("resultJson is not valid JSON.") from exc

    result_urls = parsed.get("resultUrls")
    if not result_urls or not isinstance(result_urls, list):
        raise RuntimeError("resultJson does not contain resultUrls.")

    return result_urls


def _download_image(url: str) -> bytes:
    try:
        response = requests.get(url, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download result image: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download result image (status code {response.status_code}).")

    return response.content


def _image_bytes_to_tensor(image_bytes: bytes) -> torch.Tensor:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            rgb_image = img.convert("RGB")
            tensor = torch.frombuffer(rgb_image.tobytes(), dtype=torch.uint8)
            tensor = tensor.view(rgb_image.height, rgb_image.width, 3).float() / 255.0
            return tensor.unsqueeze(0)
    except Exception as exc:
        raise RuntimeError("Failed to decode result image.") from exc
