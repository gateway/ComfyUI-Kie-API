# KIE Kling Elements

Build one Kling element payload from images or video.

## Inputs
- `name` (STRING): element name used in prompts with `@name` // super important must be element_name so element_dog then use @element_dog in the prompt
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
