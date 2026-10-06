import json
from typing import Any, Tuple

from .http import requests


API_URL = "https://api.kie.ai/api/v1/chat/credit"


def _fetch_remaining_credits(api_key: str) -> Tuple[str, int]:
    try:
        response = requests.get(
            API_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=30
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call remaining credits endpoint: {exc}") from exc

    try:
        payload: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Remaining credits endpoint did not return valid JSON.") from exc

    code = payload.get("code")
    msg = payload.get("msg")
    data = payload.get("data")

    if code != 200:
        raise RuntimeError(f"Remaining credits endpoint returned error code {code}: {msg}")

    try:
        credits_remaining = int(data)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Remaining credits value is not an integer.") from exc

    formatted_json = json.dumps(payload, indent=2, ensure_ascii=False)
    return formatted_json, credits_remaining


_logged_balances: dict = {}


def _log_remaining_credits(log: bool, record_data: dict[str, Any], api_key: str, log_fn) -> None:
    """Log the remaining balance, once per task.

    The shared poller in `jobs.py` and several model modules both report the
    balance for the same task record, so the task id (and value) is remembered to
    keep the log free of repeated lines.
    """
    if not log:
        return

    task_id = record_data.get("taskId")

    try:
        remaining = record_data.get("remainedCredits")
        if remaining is None:
            _raw, remaining = _fetch_remaining_credits(api_key)

        if task_id is not None and _logged_balances.get(task_id) == remaining:
            return
        if task_id is not None:
            _logged_balances[task_id] = remaining

        log_fn(True, f"Remaining credits: {remaining}")
    except Exception as exc:
        log_fn(True, f"Failed to fetch remaining credits: {exc}")
