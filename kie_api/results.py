"""Shared helpers for parsing KIE job results."""

import json
from typing import Any


def _extract_result_urls(record_data: dict[str, Any]) -> list[str]:
    """Extract the resultUrls list from a recordInfo payload."""
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
