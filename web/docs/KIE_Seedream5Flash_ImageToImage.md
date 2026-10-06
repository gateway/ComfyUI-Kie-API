# KIE Seedream 5.0 Flash Image-To-Image

Fast, low-cost image editing with Seedream 5.0 Flash
(KIE model id `seedream/5-flash-image-to-image`).

## Inputs
- `prompt` (STRING, required): Edit instruction, 3-3000 characters.
- `images` (IMAGE, required): Reference image batch, up to 10 images.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `resolution` (COMBO, optional): `1K`, `1.5K` or `2K` (sent to the API as `size`) (default: `1K`). Flash exposes
  resolution through the API's own `size` field (exposed here as `resolution`, like every Seedream 5 node).
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- Each input image is uploaded to KIE before the task is created; a batch with more
  than 10 images is rejected before anything is uploaded or billed.
- The node logs both the credit cost of the task (`creditsConsumed`) and the
  remaining balance when `log` is on.
- Flash also understands positional markers (bounding boxes, arrows) inside the
  prompt for targeted edits.
