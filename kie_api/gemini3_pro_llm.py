"""Gemini 3 Pro chat completions helper."""

import json
from typing import Any

from .auth import _load_api_key
from .http import TransientKieError, requests
from .audio import _coerce_audio_to_wav_bytes
from .log import _log
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_audio, _upload_image, _upload_video
from .video import _coerce_video_to_mp4_bytes

CHAT_COMPLETIONS_URLS = {
    "gemini-3-pro": "https://api.kie.ai/gemini-3-pro/v1/chat/completions",
    "gemini-3-flash": "https://api.kie.ai/gemini-3-flash/v1/chat/completions",
    "gemini-2.5-pro": "https://api.kie.ai/gemini-2.5-pro/v1/chat/completions",
    "gemini-2.5-flash": "https://api.kie.ai/gemini-2.5-flash/v1/chat/completions",
}
REASONING_EFFORT_OPTIONS = ["low", "high"]
ROLE_OPTIONS = ["developer", "system", "user", "assistant", "tool"]
MODEL_OPTIONS = list(CHAT_COMPLETIONS_URLS.keys())


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


def _format_json_for_output(payload: Any) -> str:
    if payload is None:
        return ""
    try:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    except TypeError:
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def _normalize_messages(
    prompt: str,
    messages_json: str | None,
    role: str,
    image_urls: list[str],
    video_urls: list[str],
) -> list[dict[str, Any]]:
    if messages_json:
        data = _parse_json_optional(messages_json, "messages_json")
        if not isinstance(data, list):
            raise RuntimeError("messages_json must be a JSON array of message objects.")
        return data

    if role not in ROLE_OPTIONS:
        raise RuntimeError("Invalid role. Use the pinned enum options.")

    prompt_text = (prompt or "").strip()
    if not prompt_text and not image_urls and not video_urls:
        raise RuntimeError("prompt or media input is required when messages_json is not provided.")

    content: list[dict[str, Any]] = []
    if prompt_text:
        content.append({"type": "text", "text": prompt_text})
    for url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    for url in video_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})

    return [
        {
            "role": role,
            "content": content,
        }
    ]


def run_gemini3_pro_chat(
    *,
    model: str = "gemini-3-pro",
    prompt: str,
    messages_json: str | None = None,
    role: str = "user",
    images: Any | None = None,
    video: Any | None = None,
    audio: Any | None = None,
    stream: bool = True,
    include_thoughts: bool = True,
    reasoning_effort: str = "high",
    enable_google_search: bool = False,
    response_format_json: str | None = None,
    log: bool = True,
) -> tuple[str, str, str]:
    """Run a Gemini 3 Pro chat completion request.

    Returns:
        (content_text, reasoning_text, data_json)
    """
    if model not in CHAT_COMPLETIONS_URLS:
        raise RuntimeError("Invalid model. Use the pinned enum options.")
    if reasoning_effort not in REASONING_EFFORT_OPTIONS:
        raise RuntimeError("Invalid reasoning_effort. Use the pinned enum options.")

    response_format_payload = _parse_json_optional(response_format_json, "response_format_json")
    if enable_google_search and response_format_payload is not None:
        raise RuntimeError("response_format cannot be used with tools.")
    if model == "gemini-3-flash" and response_format_payload is not None:
        raise RuntimeError("response_format is not supported for gemini-3-flash.")

    api_key = _load_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    image_urls: list[str] = []
    video_urls: list[str] = []
    audio_urls: list[str] = []

    if messages_json:
        if images is not None or video is not None or audio is not None:
            raise RuntimeError("media inputs cannot be used with messages_json.")
    else:
        if images is not None:
            if not hasattr(images, "shape"):
                raise RuntimeError("images input must be a tensor batch.")
            if images.dim() != 4 or images.shape[-1] != 3:
                raise RuntimeError("images input must have shape [B, H, W, 3].")
            total_images = images.shape[0]
            if total_images > 0:
                _log(log, f"Uploading {total_images} image(s) for {model}...")
            for idx in range(total_images):
                png_bytes = _image_tensor_to_png_bytes(images[idx])
                url = _upload_image(api_key, png_bytes)
                image_urls.append(url)
                _log(log, f"Image {idx + 1} upload success: {_truncate_url(url)}")

        if video is not None:
            video_bytes, source = _coerce_video_to_mp4_bytes(video)
            _log(log, f"Uploading video for {model} ({source})...")
            video_url = _upload_video(api_key, video_bytes)
            video_urls.append(video_url)
            _log(log, f"Video upload success: {_truncate_url(video_url)}")

        if audio is not None:
            audio_bytes, source = _coerce_audio_to_wav_bytes(audio)
            _log(log, f"Uploading audio for {model} ({source})...")
            audio_url = _upload_audio(api_key, audio_bytes)
            audio_urls.append(audio_url)
            _log(log, f"Audio upload success: {_truncate_url(audio_url)}")

    messages = _normalize_messages(
        prompt,
        messages_json,
        role,
        image_urls,
        video_urls + audio_urls,
    )

    payload: dict[str, Any] = {
        "messages": messages,
        "stream": bool(stream),
        "include_thoughts": bool(include_thoughts),
    }
    if model != "gemini-2.5-flash":
        payload["reasoning_effort"] = reasoning_effort
    elif log:
        _log(log, "reasoning_effort is not supported for gemini-2.5-flash; skipping.")
    if enable_google_search:
        payload["tools"] = [{"type": "function", "function": {"name": "googleSearch"}}]
    if response_format_payload is not None:
        payload["response_format"] = response_format_payload

    if log:
        _log(log, f"Gemini model selected: {model}")

    try:
        response = requests.post(
            CHAT_COMPLETIONS_URLS[model],
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
        return (str(content), str(reasoning), _format_json_for_output(payload_json))

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
    raw_json = _format_json_for_output(last_payload) if last_payload is not None else ""

    if log:
        _log(log, f"{model} response length: {len(content_text)} chars")

    return (content_text, reasoning_text, raw_json)
