## KIE Seedream 4.5 Edit

Edit an input image (or batch of images) using Seedream 4.5.

### Inputs
- **prompt** (STRING, required): Edit prompt text (max 3000 chars).
- **images** (IMAGE, required): Source image batch. Up to 14 images are uploaded; extra images are ignored.
- **aspect_ratio** (COMBO, optional): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `2:3`, `3:2`, `21:9` (default: `1:1`).
- **quality** (COMBO, optional): `basic`, `high` (default: `basic`).
- **log** (BOOLEAN, optional): Enable helper logging (default: `true`).

### Outputs
- **IMAGE**: ComfyUI image tensor (BHWC float32, 0..1).

### Helper behavior
- Uploads up to 14 images and sends all uploaded URLs in `input.image_urls`.
- If more than 14 images are provided, only the first 14 are used and a log message is emitted.
