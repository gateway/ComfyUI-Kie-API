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
    key_norm = str(key).strip().lower()
    if not key_norm:
        return None
    prompt_match = re.match(r"^(?:p|prompt)[\s_\-]*([1-9]\d*)$", key_norm)
    if prompt_match:
        match = prompt_match
    else:
        match = re.match(r"^([1-9]\d*)$", key_norm)
    if not match:
        return None
    try:
        index = int(match.group(1))
    except ValueError:
        return None
    if index < 1:
        return None
    return index


def parse_prompts_json(text: Any, max_items: int = 9, strict: bool = False, debug: bool = False) -> list[str]:
    if max_items < 1:
        raise ValueError("max_items must be at least 1.")

    original_text = text
    flattened = False
    if isinstance(text, (list, tuple)):
        flattened = True
        text = "\n".join("" if item is None else str(item) for item in text)
    elif isinstance(text, dict):
        if "text" in text:
            text = text.get("text")
        elif "value" in text:
            text = text.get("value")
        else:
            text = str(text)
    elif not isinstance(text, str):
        text = str(text)

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
    debug_lines: list[str] = []
    if debug:
        inspector_lines: list[str] = []
        inspector_lines.append(f"input_type={type(original_text).__name__}")
        if isinstance(original_text, (list, tuple)):
            list_len = len(original_text)
            first_item = original_text[0] if list_len else None
            inspector_lines.append(f"list_len={list_len}")
            inspector_lines.append(f"first_item_type={type(first_item).__name__}")
            inspector_lines.append(f"first_item_repr_prefix={repr(first_item)[:200]}")
        elif isinstance(original_text, dict):
            keys_preview = list(original_text.keys())[:20]
            inspector_lines.append(f"dict_keys_preview={keys_preview}")
        inspector_lines.append("normalized_type=str")
        inspector_lines.append(f"normalized_len={len(raw)}")
        inspector_lines.append(f"normalized_repr_prefix={repr(raw[:200])}")
        inspector_lines.append(f"first_brace_index={raw.find('{')}")
        inspector_lines.append(f"first_bracket_index={raw.find('[')}")
        inspector_lines.append(f"ordinals_prefix={[ord(c) for c in raw[:30]]}")
        print("[KIE Parse Prompt Grid JSON Input]", " ".join(inspector_lines))
        debug_lines.append(f"input_type={type(text).__name__}")
        debug_lines.append(f"normalized_length={len(raw)}")
        if flattened:
            debug_lines.append("flattened_input=list_or_tuple")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_code_fences(raw)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = _extract_first_json(cleaned)
            if extracted is not None:
                if debug:
                    print(
                        "[KIE Parse Prompt Grid JSON Extracted]",
                        f"extracted_repr_prefix={repr(extracted[:200])}",
                    )
                try:
                    payload = json.loads(extracted)
                except json.JSONDecodeError:
                    payload = None

    if payload is None:
        raw_no_struct = "{" not in raw and "[" not in raw
        raw_looks_like_body = raw.lstrip().startswith("\"") and "\":" in raw
        if raw_no_struct and raw_looks_like_body:
            raw_trimmed = raw.rstrip()
            if raw_trimmed.endswith(","):
                raw_trimmed = raw_trimmed[:-1].rstrip()
            raw_wrapped = "{" + raw_trimmed + "}"
            if debug:
                debug_lines.append("wrapped_body=true")
                debug_lines.append(f"wrapped_len={len(raw_wrapped)}")
            try:
                payload = json.loads(raw_wrapped)
            except json.JSONDecodeError:
                payload = None

    if payload is None:
        raise ValueError("Failed to parse JSON from json_text. Ensure the input contains a JSON object or array.")

    if isinstance(payload, str):
        nested = payload.strip()
        if nested.startswith("{") or nested.startswith("["):
            try:
                payload = json.loads(nested)
            except json.JSONDecodeError:
                pass

    prompts: list[str] = []

    def add_prompt(value: Any) -> None:
        text_value = _coerce_prompt_text(value)
        if text_value:
            prompts.append(text_value)

    if isinstance(payload, list):
        if debug:
            debug_lines.append("payload_type=list")
        for item in payload:
            add_prompt(item)
    elif isinstance(payload, dict):
        if debug:
            keys_preview = list(payload.keys())[:20]
            debug_lines.append(f"payload_type=dict keys_preview={keys_preview}")
        if isinstance(payload.get("prompts"), list):
            for item in payload["prompts"]:
                add_prompt(item)
        else:
            keyed_items: list[tuple[int, Any]] = []
            for key, value in payload.items():
                index = _extract_prompt_index(key)
                if index is None or index > max_items:
                    continue
                keyed_items.append((index, value))
            keyed_items.sort(key=lambda item: item[0])
            for _index, value in keyed_items:
                add_prompt(value)
            if debug:
                debug_lines.append(f"matched_indices={[idx for idx, _ in keyed_items]}")
    else:
        raise ValueError("JSON must be a list or object.")

    prompts = prompts[:max_items]
    if not prompts and strict:
        debug_suffix = ""
        if debug and debug_lines:
            debug_suffix = " " + " ".join(debug_lines)
        raise ValueError(
            "No prompts found in json_text. Supported keys: prompts (array), prompt1/prompt_1/p1, numeric keys."
            + debug_suffix
        )
    if debug:
        debug_lines.append(f"prompt_count={len(prompts)}")
        print("[KIE Parse Prompt Grid JSON]", " ".join(debug_lines))
    return prompts
