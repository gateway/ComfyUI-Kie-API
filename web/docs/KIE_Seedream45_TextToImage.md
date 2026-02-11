# KIE Seedream 4.5 Text-To-Image

Generate an image from a text prompt using Seedream 4.5.

## Inputs
- `prompt` (STRING, required): Generation prompt text.
- `aspect_ratio` (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- `quality` (COMBO, optional): `basic`, `high` (default: `basic`).
- `log` (BOOLEAN, optional): Enable helper logging (default: `true`).

## Outputs
- `image` (IMAGE): ComfyUI image tensor (BHWC float32, 0..1).

## Notes
- This node is text-to-image only (no image input required).
- Polling and timeout are handled internally by shared helpers.
