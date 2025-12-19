"""Shared logging helpers for KIE API modules."""


def _log(enabled: bool, msg: str) -> None:
    """Log a message to stdout when verbose logging is enabled."""
    if enabled:
        print(f"[KIE] {msg}")
