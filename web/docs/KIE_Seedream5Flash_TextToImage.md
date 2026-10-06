# KIE Seedream 5.0 Flash Text-To-Image

Fast, low-cost text-to-image generation with Seedream 5.0 Flash
(KIE model id `seedream/5-flash-text-to-image`).

## Inputs
- `prompt` (STRING, required): Generation prompt, 3-3000 characters.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `size` (COMBO, optional): `1K`, `1.5K` or `2K` (default: `1K`). Flash exposes
  resolution as a size tier; there is no `quality` enum like Pro/Lite.
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- The node logs both the credit cost of the task (`creditsConsumed`) and the
  remaining balance when `log` is on.
- Flash is the fast/cheap tier of the Seedream 5 family; use Pro or Lite when
  maximum quality matters more than latency or price.
