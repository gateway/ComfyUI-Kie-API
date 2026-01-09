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

    def _strip_code_fences(value: str) -> str:
        stripped = value.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip().startswith("```"):
                return "\n".join(lines[1:-1]).strip()
        return stripped

    def _extract_first_json(value: str) -> str | None:
        start = None
        opening = None
        for idx, ch in enumerate(value):
            if ch == "{" or ch == "[":
                start = idx
                opening = ch
                break
        if start is None or opening is None:
            return None

        closing = "}" if opening == "{" else "]"
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(value)):
            ch = value[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == "\"":
                    in_string = False
                continue

            if ch == "\"":
                in_string = True
                continue
            if ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return value[start:idx + 1]
        return None

    payload = None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_code_fences(raw)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = _extract_first_json(cleaned)
            if extracted is not None:
                try:
                    payload = json.loads(extracted)
                except json.JSONDecodeError:
                    payload = None

    if payload is None:
        raise ValueError("Failed to parse JSON from json_text. Ensure the input contains a JSON object or array.")

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
