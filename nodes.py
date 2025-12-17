import json
from pathlib import Path
from typing import Any, Tuple

import requests


KIE_KEY_PATH = Path(__file__).resolve().parent / "config" / "kie_key.txt"
API_URL = "https://api.kie.ai/api/v1/chat/credit"


def _load_api_key() -> str:
    try:
        api_key = KIE_KEY_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "KIE API key not found. Please create config/kie_key.txt with your API key."
        ) from exc
    if not api_key:
        raise RuntimeError("KIE API key file is empty. Please add your key to config/kie_key.txt.")
    return api_key


def _fetch_remaining_credits(api_key: str) -> Tuple[str, int]:
    try:
        response = requests.get(
            API_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=30
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call remaining credits endpoint: {exc}") from exc

    raw_text = response.text
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

    return raw_text, credits_remaining


def _log(enabled: bool, msg: str) -> None:
    if enabled:
        print(f"[KIE] {msg}")


class KIE_GetRemainingCredits:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"log": ("BOOLEAN", {"default": True})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("raw_json", "credits_remaining")
    FUNCTION = "get_remaining_credits"
    CATEGORY = "kie/api"

    def get_remaining_credits(self, log: bool):
        _log(log, "Requesting remaining credits...")
        api_key = _load_api_key()
        raw_json, credits_remaining = _fetch_remaining_credits(api_key)
        _log(log, f"Credits remaining: {credits_remaining}")
        return (raw_json, credits_remaining)


NODE_CLASS_MAPPINGS = {"KIE_GetRemainingCredits": KIE_GetRemainingCredits}
NODE_DISPLAY_NAME_MAPPINGS = {"KIE_GetRemainingCredits": "KIE Get Remaining Credits"}
