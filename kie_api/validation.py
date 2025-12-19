"""Shared validation helpers for KIE API modules."""


def _validate_prompt(prompt: str, *, max_length: int) -> None:
    """Ensure prompts are present and below the specified maximum length."""
    if not prompt:
        raise RuntimeError("Prompt is required.")
    if len(prompt) > max_length:
        raise RuntimeError(f"Prompt exceeds the maximum length of {max_length} characters.")
