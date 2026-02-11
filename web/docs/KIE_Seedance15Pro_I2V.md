# KIE Seedance 1.5 Pro (I2V/T2V)

Generate video from a prompt using Seedance 1.5 Pro, with optional reference images.

## Inputs
- `prompt` (STRING, required): Prompt text (minimum 3 characters).
- `images` (IMAGE, optional): Reference image batch; up to 2 images are uploaded (extra images are ignored).
- `aspect_ratio` (COMBO, optional): `1:1`, `21:9`, `4:3`, `3:4`, `16:9`, `9:16` (default: `1:1`).
- `resolution` (COMBO, optional): `480p`, `720p` (default: `720p`).
- `duration` (COMBO, optional): `4`, `8`, `12` seconds (default: `8`).
- `fixed_lens` (BOOLEAN, optional): Lock camera lens behavior.
- `generate_audio` (BOOLEAN, optional): Enable audio generation.
- `log` (BOOLEAN, optional): Enable helper logging (default: `true`).

## Outputs
- `video` (VIDEO): SaveVideo-compatible ComfyUI video output.

## Notes
- No images connected = text-to-video mode.
- If images are connected, they are uploaded and sent as `input_urls`.
- Input enums are strict and validated before createTask submission.
