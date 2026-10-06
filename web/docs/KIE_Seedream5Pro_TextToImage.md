# KIE Seedream 5.0 Pro Text-To-Image

Generate one image from a text prompt using Seedream 5.0 Pro (KIE model id
`seedream/5-pro-text-to-image`).

## Inputs
- `prompt` (STRING, required): Generation prompt, 3-3000 characters.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `quality` (COMBO, optional): `basic` (1K) or `high` (2K) (default: `basic`).
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- Text-to-image only (no image input required).
- Polling, download, decoding and remaining-credit logging are handled by the
  shared helpers (`jobs`, `images`, `results`, `credits`).
- KIE billing for this endpoint: 7 credits per 1K image, 14 per 2K image.
- `nsfw_checker: false` disables KIE's content filter (results come straight from the model).
