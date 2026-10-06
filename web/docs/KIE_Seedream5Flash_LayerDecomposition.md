# KIE Seedream 5.0 Flash Layer Decomposition

Turn one flat image into a base image plus up to 16 transparent layers
(KIE model id `seedream/5-flash-layer-decomposition`).

## Inputs
- `image` (IMAGE, required): Source image. Exactly one image is used; extra
  images in the batch are ignored with a log line.
- `prompt` (STRING, optional): What to separate. Empty means the model picks the
  main elements itself. Supports `<bbox>x1 y1 x2 y2</bbox>` with normalised
  0-1000 coordinates, e.g.
  `Separate the title text <bbox>179 58 809 197</bbox> and the parrot <bbox>330 274 641 991</bbox>`.
- `resolution` (COMBO, optional): `auto`, `1K`, `1.5K` or `2K` (sent to the API as `size`) (default: `auto`).
- `output_format` (COMBO, optional): `png`, `jpeg` — base image only, layers are
  always PNG (default: `jpeg`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `images` (IMAGE): batch in the order the API returned the images: entry 0 is
  the full base image, the rest are one plate per element, every one of them at
  full canvas size.
- `masks` (MASK): matching batch, inverse alpha (1.0 = transparent, 0.0 =
  opaque) — the same convention as the rest of the pack.
- `layer_info` (STRING): JSON report per image (`index`, `z_index`, `name`,
  `description`, `size`, `origin`, `bounding_box`, `url`).

## Measured behaviour (Flash vs Pro)
- **Flash returns no layer metadata**: `resultJson` carries only `resultUrls`,
  with no `layers_data`, no names, no bounding boxes and no `z_index`. The layers
  are full-canvas plates: each one draws its element at its own scale and
  position, which is *not* the scale of the base image (a measured run put a
  "FARO" text plate far larger and higher than the text in the base), so the
  batch **cannot be recomposed by simply stacking it** — use the plates
  individually, rescaling/placing them yourself.
- The **Pro variant** (`KIE_Seedream5Pro_LayerDecomposition`) does return
  `layers_data` with names, `z_index` and bounding boxes, and its result
  recomposes into the original image when stacked (verified end to end).
- Entry 0 (the base) is itself a re-render of the source image, not a byte copy:
  expect small differences even before you touch the layers.
- Billing is per returned image: a request reserves base + 16 layers and settles
  to the images actually delivered, so heavy decompositions cost more than a
  plain generation.
- The node logs the credit cost of the task (`creditsConsumed`) and the remaining
  balance when `log` is on.
