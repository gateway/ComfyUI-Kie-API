# KIE Grok Imagine (I2I)

Generate one or more images from a source image using Grok Imagine.

## Inputs
- `images` (IMAGE, required): Source image batch. Only the first image is uploaded.
- `prompt` (STRING, optional): Edit/style prompt text. Max length: `390000`.
- `log` (BOOLEAN, optional): Enable helper logging (default: `true`).

## Outputs
- `image` (IMAGE): ComfyUI image batch (BHWC float32, 0..1).
- `task_id` (STRING): KIE task id from `createTask`, for chaining into Grok I2V.

## Notes
- If multiple input images are connected, the node uploads only the first image and logs that choice.
- The node downloads all returned `resultUrls` and returns them as one `IMAGE` batch.
- This is the intended upstream source for Grok I2V `task_id + index` chaining.
