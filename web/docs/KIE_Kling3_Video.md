# KIE Kling 3.0 (Video)

Generate Kling 3.0 videos in single-shot or multi-shot mode.

> Status: Experimental (development pass). Not production-ready yet.

## Inputs
- `mode` (COMBO): `std` or `pro`
- `aspect_ratio` (COMBO): `1:1`, `9:16`, `16:9`
- `duration` (COMBO): `3` to `15`
- `multi_shots` (BOOLEAN): enables multi-shot mode
- `prompt` (STRING): single-shot prompt
- `shots_text` (STRING, optional): multi-shot lines:
  - `duration | prompt`
  - or `label | duration | prompt`
- `first_frame` (IMAGE, optional): start frame
- `last_frame` (IMAGE, optional): end frame (single-shot only)
- `sound` (BOOLEAN, optional): single-shot only
- `element` (KIE_ELEMENT, optional): one element
- `elements` (KIE_ELEMENTS, optional): batched elements
- `log` (BOOLEAN, optional)

## Rules
- `multi_shots=true`:
  - `last_frame` is invalid
  - `sound` is invalid
  - shot durations are summed automatically and sent as the final payload duration
- If both start and end frames are provided, aspect ratio is auto-adapted from frames.
- `@element_name` references in prompt(s) must match provided elements.
- Multi-shot total duration must stay within `3..15` seconds.

## Cost note
- Kling 3.0 usage cost is tied to generated duration.
- In multi-shot mode, cost follows the computed total shot duration (max 15s).

## Output
- `VIDEO`: SaveVideo-compatible ComfyUI video output.
