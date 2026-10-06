# KIE Seedream 5.0 Lite Text-To-Image

Generate one image from a text prompt using Seedream 5.0 Lite
(KIE model id `seedream/5-lite-text-to-image`).

Cheaper tier than Pro, with higher resolution steps: one `ultra` render is the
way to get a 4K image out of this family.

## Inputs
- `prompt` (STRING, required): Generation prompt, 3-3000 characters.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `resolution` (COMBO, optional): `2K` (sent as `quality: basic`), `3K` (`high`) or `4K` (`ultra`) (default: `2K`).
- `output_format` (COMBO, optional): `png`, `jpeg` (default: `png`).
- `nsfw_checker` (BOOLEAN, optional): enable KIE content filtering (default: `true`).
- `log` (BOOLEAN, optional): enable helper logging (default: `true`).
- `poll_interval_s` / `timeout_s` (hidden widget inputs): polling cadence and hard timeout.

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- The node logs both the credit cost of the task (`creditsConsumed`) and the
  remaining balance when `log` is on.
- `resolution: 4K` (API `quality: ultra`) renders 4K; expect a longer polling time than the 2K tier.
- Aspect ratios and resolution values were verified against the live API, not only
  against the docs (21:9 and `ultra` are accepted, and `ultra` is Lite-only).
