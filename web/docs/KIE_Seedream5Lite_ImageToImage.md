# KIE Seedream 5.0 Lite Image-To-Image

Edit one or more reference images with a text instruction using Seedream 5.0 Lite
(KIE model id `seedream/5-lite-image-to-image`).

Cheaper tier than Pro, and the one that takes the most references: up to 14.

## Inputs
- `prompt` (STRING, required): Edit instruction, 3-3000 characters.
- `images` (IMAGE, required): Reference image batch, up to 14 images. Extra
  references beyond the first are billed separately by KIE.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `resolution` (COMBO, optional): `2K` (sent as `quality: basic`), `3K` (`high`) or `4K` (`ultra`) (default: `2K`).
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- Each input image is uploaded to KIE before the task is created; the module
  truncates to the first 14 images and logs it when it does.
- The node logs both the credit cost of the task (`creditsConsumed`) and the
  remaining balance when `log` is on.
- Keep the instruction focused on what must change and what must be preserved —
  with up to 14 references you can mix subjects, styles, materials and poses.
