# KIE Grok Imagine (T2I)

Generate one or more images from a text prompt using Grok Imagine.

## Inputs
- `prompt` (STRING, required): Generation prompt text. Max length: `5000`.
- `aspect_ratio` (COMBO, optional): `2:3`, `3:2`, `1:1`, `9:16`, `16:9` (default: `1:1`).
- `log` (BOOLEAN, optional): Enable helper logging (default: `true`).

## Outputs
- `image` (IMAGE): ComfyUI image batch (BHWC float32, 0..1).
- `task_id` (STRING): KIE task id from `createTask`, for chaining into Grok I2V.

## Notes
- The node downloads all returned `resultUrls` and returns them as one `IMAGE` batch.
- This is the intended upstream source for Grok I2V `task_id + index` chaining.
- Polling and timeout are handled internally by shared helpers.
