"""Shared validation helpers for KIE API modules."""

import torch


def _validate_prompt(prompt: str, *, max_length: int) -> None:
    """Ensure prompts are present and below the specified maximum length."""
    if not prompt:
        raise RuntimeError("Prompt is required.")
    if len(prompt) > max_length:
        raise RuntimeError(f"Prompt exceeds the maximum length of {max_length} characters.")


def _validate_image_tensor_batch(images: torch.Tensor | None) -> torch.Tensor:
    """Ensure images are a non-empty [B, H, W, 3] tensor batch."""
    if images is None:
        raise RuntimeError("images input is required.")
    if not isinstance(images, torch.Tensor):
        raise RuntimeError("images input must be a tensor batch.")
    if images.dim() != 4 or images.shape[-1] != 3:
        raise RuntimeError("images input must have shape [B, H, W, 3].")
    if images.shape[0] < 1:
        raise RuntimeError("images input batch is empty.")
    return images
