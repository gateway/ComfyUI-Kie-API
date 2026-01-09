import json
import re
from typing import Any


def _coerce_prompt_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    try:
        return str(value).strip()
    except Exception:
        return ""


def _extract_prompt_index(key: Any) -> int | None:
    if not isinstance(key, str):
        return None
    normalized = key.strip().lower()
    if not normalized:
        return None
    prompt_match = re.match(r"^\\s*(?:p|prompt)\\s*[_\\-\\s]*([1-9]\\d*)\\s*$", normalized, re.IGNORECASE)
    if prompt_match:
        match = prompt_match
    else:
        match = re.match(r"^\\s*([1-9]\\d*)\\s*$", normalized)
    if not match:
        return None
    try:
        index = int(match.group(1))
    except ValueError:
        return None
    if index < 1:
        return None
    return index


def parse_prompts_json(text: str, max_items: int = 9, strict: bool = False) -> list[str]:
    if max_items < 1:
        raise ValueError("max_items must be at least 1.")

    raw = text.strip() if isinstance(text, str) else ""
    if not raw:
        if strict:
            raise ValueError("json_text is empty.")
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse JSON from json_text.") from exc

    prompts: list[str] = []

    def add_prompt(value: Any) -> None:
        text_value = _coerce_prompt_text(value)
        if text_value:
            prompts.append(text_value)

    if isinstance(payload, list):
        for item in payload:
            add_prompt(item)
    elif isinstance(payload, dict):
        if isinstance(payload.get("prompts"), list):
            for item in payload["prompts"]:
                add_prompt(item)
        else:
            keyed_items: list[tuple[int, Any]] = []
            for key, value in payload.items():
                index = _extract_prompt_index(key)
                if index is None:
                    continue
                keyed_items.append((index, value))
            keyed_items.sort(key=lambda item: item[0])
            for _index, value in keyed_items:
                add_prompt(value)
    else:
        raise ValueError("JSON must be a list or object.")

    prompts = prompts[:max_items]
    if not prompts and strict:
        raise ValueError(
            "No prompts found in json_text. Supported keys: prompts (array), prompt1/prompt_1/p1, numeric keys."
        )
    return prompts
