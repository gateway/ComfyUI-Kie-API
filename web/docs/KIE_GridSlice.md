# KIE Grid Slice

Slice a grid image into equal tiles, with optional border cropping and gutter removal.

## Inputs
- **IMAGE**: Grid image batch (BHWC float32 0–1).
- **grid**: Layout (`2x2` or `3x3`).
- **outer_crop_px**: Pixels trimmed from each side before slicing.
- **gutter_px**: Pixels removed between tiles inside the grid.
- **order**: `row-major` (top-left → right, then down) or `column-major` (top-left → down, then right).
- **process_batch**: `first` to slice only the first image in the batch, `all` to slice every image and concatenate tiles.
- **log**: Enable console logging.

## Outputs
- **IMAGE**: Tile batch (4 tiles for `2x2`, 9 tiles for `3x3` per processed image), BHWC float32 in `[0, 1]`.

## Behavior
- Applies outer crop, then removes gutters, then slices into tiles.
- Uses floor sizing when dimensions are not perfectly divisible; extra pixels on the right/bottom are dropped.
- Validates crop/gutter to avoid zero or negative tile sizes; raises readable errors when impossible.
- Ordering controls the tile sequence in the output batch. For example, `row-major` on `2x2` produces tiles in this order:
  1. Top-left
  2. Top-right
  3. Bottom-left
  4. Bottom-right
