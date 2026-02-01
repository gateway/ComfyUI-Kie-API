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


def _log_remaining_credits(log: bool, record_data: dict[str, Any], api_key: str, log_fn) -> None:
    if not log:
        return

    remaining = record_data.get("remainedCredits")
    if remaining is not None:
        log_fn(True, f"Remaining credits: {remaining}")
        return

    try:
        _raw, credits_remaining = _fetch_remaining_credits(api_key)
        log_fn(True, f"Remaining credits: {credits_remaining}")
    except Exception as exc:
        log_fn(True, f"Failed to fetch remaining credits: {exc}")
