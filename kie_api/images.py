from io import BytesIO

import torch
from PIL import Image


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
            rgb_bytes = rgb_image.tobytes()

            tensor = torch.frombuffer(rgb_bytes, dtype=torch.uint8).clone()
            tensor = tensor.view(rgb_image.height, rgb_image.width, 3).float() / 255.0
            return tensor.unsqueeze(0)
    except Exception as exc:
        raise RuntimeError("Failed to decode result image.") from exc
