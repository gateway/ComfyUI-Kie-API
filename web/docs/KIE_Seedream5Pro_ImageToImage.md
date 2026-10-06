# KIE Seedream 5.0 Pro Image-To-Image

Edit one or more reference images with a text instruction using Seedream 5.0 Pro
(KIE model id `seedream/5-pro-image-to-image`).

## Inputs
- `prompt` (STRING, required): Edit instruction, 3-3000 characters.
- `images` (IMAGE, required): Reference image batch, up to 10 images. The first
  reference is included in the base price; KIE bills each additional input image.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `resolution` (COMBO, optional): `1K` (sent to the API as `quality: basic`) or `2K` (`quality: high`) (default: `1K`).
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- Each input image is uploaded to KIE (`/api/v1/jobs/upload` path helpers) before
  the task is created; the module truncates to the first 10 images and logs it.
- KIE billing for this endpoint: 7 credits per 1K image, 14 per 2K image.
- Keep the instruction focused on what must change and what must be preserved —
  multi-reference input lets you mix subjects, styles or materials.
