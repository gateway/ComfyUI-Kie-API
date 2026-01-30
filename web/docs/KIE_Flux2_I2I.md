# KIE Flux 2 (Image-to-Image)

Generate an image from one or more input images using Flux 2 Pro or Flux 2 Flex.

## Inputs
- **images** (IMAGE, required): Input image batch. 1–8 images supported; all are uploaded.
- **prompt** (STRING, required): Text prompt (3–5000 characters).
- **model** (COMBO, required):  
  - `flux-2/pro-image-to-image`  
  - `flux-2/flex-image-to-image`
- **aspect_ratio** (COMBO, required): `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `3:2`, `2:3`, `auto`
- **resolution** (COMBO, required): `1K`, `2K`
- **log** (BOOLEAN, optional): Enable console logging.

## Outputs
- **IMAGE**: ComfyUI image tensor (BHWC, float32, 0–1)

## Helper behavior
- Validates prompt length and image tensor shape.
- Uploads up to 8 images and passes their URLs in `input_urls`.
- Polls the task until completion, then downloads and decodes the output image.
