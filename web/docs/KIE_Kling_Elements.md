# KIE Kling Elements

Build one Kling element payload from images or video.

## Inputs
- `name` (STRING): element name used in prompts with `@name`
- `description` (STRING, optional)
- `images` (IMAGE, optional): image element source (2-4 images)
- `video` (VIDEO, optional): video element source (single clip)
- `log` (BOOLEAN, optional)

## Rules
- Provide exactly one media type:
  - images only, or
  - video only
- Using both images and video in one element raises an error.

## Outputs
- `KIE_ELEMENT`: single element payload
- `STRING`: JSON preview of the element payload
