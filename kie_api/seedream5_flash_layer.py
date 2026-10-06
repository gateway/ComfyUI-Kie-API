"""Seedream 5.0 Flash layer decomposition helper.

Implements the Seedream 5.0 Flash layer decomposition endpoint documented at
https://docs.kie.ai/market/seedream/5-flash-layer-decomposition

Model id: `seedream/5-flash-layer-decomposition`.

Takes exactly ONE source image and returns a base image plus up to 16
transparent layers. The assembly into ComfyUI IMAGE + MASK + STRING outputs lives
in `layers.py`, shared with the Pro variant; this module only pins the model id
and its `size` tiers.
"""

import torch

from .layers import OUTPUT_FORMAT_OPTIONS, PROMPT_MAX_LENGTH, run_layer_decomposition


MODEL_NAME = "seedream/5-flash-layer-decomposition"
SIZE_OPTIONS = ["auto", "1K", "1.5K", "2K"]


def run_seedream5_flash_layer_decomposition(
    image: torch.Tensor,
    prompt: str,
    size: str,
    output_format: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> tuple[torch.Tensor, torch.Tensor, str]:
    """Split one source image into a base image plus layers (Flash).

    Returns:
        (images, masks, layer_info): IMAGE batch, MASK batch (inverse alpha) and a
        JSON string describing the layer stack.
    """
    return run_layer_decomposition(
        model_name=MODEL_NAME,
        size_options=SIZE_OPTIONS,
        image=image,
        prompt=prompt,
        size=size,
        output_format=output_format,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )
