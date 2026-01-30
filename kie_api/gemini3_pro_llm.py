"""Gemini 3 Pro chat completions helper."""

import json
from typing import Any

from .auth import _load_api_key
from .http import TransientKieError, requests
from .log import _log

CHAT_COMPLETIONS_URL = "https://api.kie.ai/gemini-3-pro/v1/chat/completions"
REASONING_EFFORT_OPTIONS = ["low", "high"]


def _parse_json_optional(raw: str | None, label: str) -> Any | None:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON.") from exc


def _normalize_messages(prompt: str, messages_json: str | None) -> list[dict[str, Any]]:
    if messages_json:
        data = _parse_json_optional(messages_json, "messages_json")
        if not isinstance(data, list):
            raise RuntimeError("messages_json must be a JSON array of message objects.")
        return data

    prompt_text = (prompt or "").strip()
    if not prompt_text:
        raise RuntimeError("prompt is required when messages_json is not provided.")
    return [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt_text}],
        }
    ]


def _validate_tools_payload(tools_payload: Any | None) -> None:
    if tools_payload is None:
        return
    if not isinstance(tools_payload, list):
        raise RuntimeError("tools_json must be a JSON array.")

    tool_names = []
    for item in tools_payload:
        if not isinstance(item, dict):
            raise RuntimeError("tools_json must be a JSON array of objects.")
        fn = (item.get("function") or {})
        if isinstance(fn, dict):
            name = fn.get("name")
            if isinstance(name, str):
                tool_names.append(name)

    if "googleSearch" in tool_names and len(tool_names) > 1:
        raise RuntimeError("googleSearch cannot be combined with other tools.")


def run_gemini3_pro_chat(
    *,
    prompt: str,
    messages_json: str | None = None,
    stream: bool = True,
    include_thoughts: bool = True,
    reasoning_effort: str = "high",
    tools_json: str | None = None,
    response_format_json: str | None = None,
    log: bool = True,
) -> tuple[str, str, str]:
    """Run a Gemini 3 Pro chat completion request.

    Returns:
        (content_text, reasoning_text, raw_json)
    """
    if reasoning_effort not in REASONING_EFFORT_OPTIONS:
        raise RuntimeError("Invalid reasoning_effort. Use the pinned enum options.")

    tools_payload = _parse_json_optional(tools_json, "tools_json")
    response_format_payload = _parse_json_optional(response_format_json, "response_format_json")
    if tools_payload is not None and response_format_payload is not None:
        raise RuntimeError("response_format cannot be used with tools.")
    _validate_tools_payload(tools_payload)

    messages = _normalize_messages(prompt, messages_json)

    payload: dict[str, Any] = {
        "messages": messages,
        "stream": bool(stream),
        "include_thoughts": bool(include_thoughts),
        "reasoning_effort": reasoning_effort,
    }
    if tools_payload is not None:
        payload["tools"] = tools_payload
    if response_format_payload is not None:
        payload["response_format"] = response_format_payload

    api_key = _load_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers=headers,
            json=payload,
            timeout=60,
            stream=bool(stream),
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call chat completions endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"chat completions returned HTTP {response.status_code}: {response.text}",
            status_code=response.status_code,
        )

    if not stream:
        try:
            payload_json: Any = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError("chat completions endpoint did not return valid JSON.") from exc

        choices = payload_json.get("choices") or []
        if not choices:
            raise RuntimeError("chat completions response did not include choices.")

        message = (choices[0].get("message") or {})
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or ""
        return (str(content), str(reasoning), json.dumps(payload_json))

    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    last_payload: Any = None

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue

        data = line[5:].strip()
        if data == "[DONE]":
            break

        try:
            chunk = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Streaming chunk did not contain valid JSON.") from exc

        last_payload = chunk
        choices = chunk.get("choices") or []
        for choice in choices:
            delta = choice.get("delta") or {}
            content_piece = delta.get("content")
            if isinstance(content_piece, str):
                content_parts.append(content_piece)
            reasoning_piece = delta.get("reasoning_content")
            if isinstance(reasoning_piece, str):
                reasoning_parts.append(reasoning_piece)

    content_text = "".join(content_parts)
    reasoning_text = "".join(reasoning_parts)
    raw_json = json.dumps(last_payload) if last_payload is not None else ""

    if log:
        _log(log, f"Gemini 3 Pro response length: {len(content_text)} chars")

    return (content_text, reasoning_text, raw_json)
