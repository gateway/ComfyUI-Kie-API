from io import BytesIO

import torch
import numpy as np
from PIL import Image

from .http import requests


def _image_bytes_to_tensor(image_bytes: bytes) -> torch.Tensor:
    """Convert image bytes into a normalized torch tensor.

    Returns:
        A tensor of shape (1, H, W, 3) with float values in [0, 1].
    Raises:
        RuntimeError: If the image cannot be decoded.
    """
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            rgb_image = img.convert("RGB")
            
            # FIX: Use numpy to create the array. This creates a writable buffer
            # automatically, resolving the PyTorch warning.
            tensor = torch.from_numpy(np.array(rgb_image))
            
            tensor = tensor.float() / 255.0
            return tensor.unsqueeze(0)
    except Exception as exc:
        raise RuntimeError("Failed to decode result image.") from exc


def _download_image(url: str) -> bytes:
    """Download a result image and return its raw bytes."""
    try:
        response = requests.get(url, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download result image: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download result image (status code {response.status_code}).")

    return response.content


def _stack_image_tensors(image_tensors: list[torch.Tensor]) -> torch.Tensor:
    """Combine decoded image tensors into one ComfyUI IMAGE batch."""
    if not image_tensors:
        raise RuntimeError("No result images were returned.")

    base_shape = tuple(image_tensors[0].shape[1:])
    for idx, tensor in enumerate(image_tensors[1:], start=1):
        if tuple(tensor.shape[1:]) != base_shape:
            raise RuntimeError(
                "Result images returned inconsistent sizes; cannot combine them into one IMAGE batch "
                f"(mismatch at index {idx})."
            )

    return torch.cat(image_tensors, dim=0)


def _download_images_as_batch(urls: list[str]) -> torch.Tensor:
    """Download multiple image URLs and return a single IMAGE batch tensor."""
    if not urls:
        raise RuntimeError("No result image URLs were returned.")

    image_tensors = [_image_bytes_to_tensor(_download_image(url)) for url in urls]
    return _stack_image_tensors(image_tensors)
