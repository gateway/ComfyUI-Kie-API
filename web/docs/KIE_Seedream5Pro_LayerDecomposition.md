# KIE Seedream 5.0 Pro Layer Decomposition

Turn one flat image into a base image plus up to 16 transparent layers using the
higher-quality Pro model (KIE model id `seedream/5-pro-layer-decomposition`).

## Inputs
- `image` (IMAGE, required): Source image. Exactly one image is used; extra
  images in the batch are ignored with a log line.
- `prompt` (STRING, optional): What to separate. Empty means the model picks the
  main elements itself. Supports `<bbox>x1 y1 x2 y2</bbox>` with normalised
  0-1000 coordinates, e.g.
  `Separate the title text <bbox>179 58 809 197</bbox> and the parrot <bbox>330 274 641 991</bbox> into independent layers`.
- `size` (COMBO, optional): `auto`, `1K`, `1.5K` or `2K` (default: `auto`).
- `output_format` (COMBO, optional): `png`, `jpeg` — base image only, layers are
  always PNG (default: `jpeg`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `images` (IMAGE): batch with the base image first and then every layer in
  ascending `z_index`. Each entry is placed on a canvas the size of the base
  image at its bounding box position, so the batch composites directly.
- `masks` (MASK): matching batch, inverse alpha (1.0 = transparent, 0.0 =
  opaque) — the same convention as the rest of the pack, with the layer's own
  alpha inside the box.
- `layer_info` (STRING): JSON report with `z_index`, `name`, `description`,
  `size`, `origin` (canvas position), `bounding_box` and `url` per layer.

## Notes
- Same contract as the Flash variant; Pro costs more per image and takes longer,
  and produces cleaner layer edges and naming.
- Billing is per returned image: a request reserves base + 16 layers and settles
  to the images actually delivered, so a decomposition needs a balance of roughly
  17x the per-image price to be accepted at all.
- The node logs the credit cost of the task (`creditsConsumed`) and the remaining
  balance when `log` is on.
