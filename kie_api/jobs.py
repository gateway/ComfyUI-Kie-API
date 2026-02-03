"""Shared job lifecycle helpers for KIE async tasks.

This module centralizes common KIE job lifecycle operations that are model-agnostic:

- Fetch `recordInfo` for a task id.
- Decide whether a task failure is likely transient.
- Poll a task until completion, failure, or timeout.

Behavior (logging text, timing, error types) is intentionally kept identical to the
original model-specific implementations.
"""

import json
import time
from typing import Any

from .http import TransientKieError, requests
from .log import _log


CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
DEFAULT_TIMEOUT_S = 1000


def _create_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    """Create a task via the KIE createTask endpoint.

    Returns:
        A tuple of (task_id, raw_response_text).
    Raises:
        RuntimeError: If the request fails, returns non-JSON, or returns an error code.
        TransientKieError: If the API responds with retryable errors (429 or >=500).
    """
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

    raw_text = response.text
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

    return task_id, raw_text


def _fetch_task_record(api_key: str, task_id: str) -> tuple[dict[str, Any], str, Any]:
    """Fetch the current record for a task.

    Returns:
        A tuple of (data_dict, raw_response_text, message_field).
    Raises:
        RuntimeError: If the request fails, returns non-JSON, or returns an error code.
        TransientKieError: If the API responds with retryable errors (429 or >=500).
    """
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
    """Determine whether a failed task should be retried.

    Returns:
        True if the failure looks transient and worth retrying, otherwise False.
    Raises:
        None.
    """
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
) -> dict[str, Any]:
    """Poll recordInfo until the task completes, fails, or times out.

    Returns:
        The task record data dict returned by recordInfo.
    Raises:
        RuntimeError: If the task times out or returns a non-retryable failure.
        TransientKieError: If the task fails with a retryable condition.
    """
    # Ensure we never poll faster than once per second to reduce server load.
    interval = poll_interval_s if poll_interval_s > 0 else 1.0
    effective_timeout_s = timeout_s if timeout_s >= DEFAULT_TIMEOUT_S else DEFAULT_TIMEOUT_S
    last_state = None
    last_log_time = start_time

    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed > effective_timeout_s:
            last_state_text = last_state if last_state is not None else "unknown"
            raise RuntimeError(
                f"Task {task_id} timed out after {effective_timeout_s}s "
                f"(last state={last_state_text}, elapsed={elapsed:.1f}s). "
                "Try increasing timeout or retry."
            )

        data, raw_json, message_field = _fetch_task_record(api_key, task_id)
        state = data.get("state")
        # Log only on state change or every 30s to give progress without noisy output.
        should_log = log and (state != last_state or (now - last_log_time) >= 30.0)
        if should_log:
            _log(
                log,
                f"Task {task_id} state: {state or 'unknown'} "
                f"(elapsed={elapsed:.1f}s)"
            )
            last_log_time = now

        last_state = state

        if state == "success":
            if log:
                _log(log, f"Task {task_id} completed (elapsed={elapsed:.1f}s)")
            return data
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
