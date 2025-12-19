"""Grid slicing utilities for ComfyUI images.

Provides tensor-only helpers so nodes remain thin wrappers.
"""

import torch

from .nanobanana import _log


def slice_grid_tensor(
    image: torch.Tensor,
    grid: str,
    outer_crop_px: int,
    gutter_px: int,
    order: str,
    process_batch: str,
    log: bool,
) -> torch.Tensor:
    """Slice a grid image tensor into tiles.

    Args:
        image: Input batch tensor with shape [B, H, W, 3].
        grid: "2x2" or "3x3".
        outer_crop_px: Pixels trimmed from each side before slicing.
        gutter_px: Pixels removed between tiles inside the grid.
        order: "row-major" or "column-major".
        process_batch: "first" or "all".
        log: Enable verbose logging via shared logger.

    Returns:
        Tensor of tiles stacked on batch dimension.
    """
    rows, cols = (2, 2) if grid == "2x2" else (3, 3)

    if image.dim() != 4 or image.shape[-1] != 3:
        raise RuntimeError("IMAGE input must have shape [B, H, W, 3].")

    batch_count = image.shape[0]
    if batch_count < 1:
        raise RuntimeError("IMAGE batch is empty.")

    if outer_crop_px < 0:
        raise RuntimeError("outer_crop_px must be >= 0.")
    if gutter_px < 0:
        raise RuntimeError("gutter_px must be >= 0.")

    targets = [image[0]] if process_batch == "first" else [image[i] for i in range(batch_count)]

    def slice_single(img: torch.Tensor) -> list[torch.Tensor]:
        if img.dim() != 3 or img.shape[2] != 3:
            raise RuntimeError("IMAGE must have shape [H, W, 3].")

        height, width, _ = img.shape
        inner_h = height - 2 * outer_crop_px
        inner_w = width - 2 * outer_crop_px
        if inner_h <= 0 or inner_w <= 0:
            raise RuntimeError("outer_crop_px is too large for the input image.")

        cropped = img[outer_crop_px:height - outer_crop_px, outer_crop_px:width - outer_crop_px, :]

        avail_w = inner_w - gutter_px * (cols - 1)
        avail_h = inner_h - gutter_px * (rows - 1)
        if avail_w <= 0 or avail_h <= 0:
            raise RuntimeError("gutter_px is too large for the cropped image.")

        tile_w = avail_w // cols
        tile_h = avail_h // rows
        if tile_w <= 0 or tile_h <= 0:
            raise RuntimeError("Computed tile dimensions are non-positive; adjust crop/gutter.")

        tiles: list[torch.Tensor] = []

        def add_tile(r_idx: int, c_idx: int):
            start_y = r_idx * (tile_h + gutter_px)
            start_x = c_idx * (tile_w + gutter_px)
            tile = cropped[start_y:start_y + tile_h, start_x:start_x + tile_w, :]
            tiles.append(tile)

        if order == "row-major":
            for r in range(rows):
                for c in range(cols):
                    add_tile(r, c)
        else:
            for c in range(cols):
                for r in range(rows):
                    add_tile(r, c)

        if log:
            _log(
                log,
                f"Sliced image into {rows}x{cols} tiles of size {tile_h}x{tile_w} "
                f"(outer_crop_px={outer_crop_px}, gutter_px={gutter_px}, order={order})",
            )

        return tiles

    all_tiles: list[torch.Tensor] = []
    for idx, img in enumerate(targets):
        tiles = slice_single(img)
        all_tiles.extend(tiles)
        if log and process_batch == "all":
            _log(log, f"Processed image {idx + 1}/{len(targets)}.")

    return torch.stack(all_tiles, dim=0)

