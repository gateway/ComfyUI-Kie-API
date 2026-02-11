# KIE Kling 3.0 (Video)

Generate Kling 3.0 videos in single-shot or multi-shot mode.

> Status: Experimental (development pass). Not production-ready yet.
> Credit Warning: Kling 3.0 can consume significant credits. Use `KIE Kling 3.0 Preflight` first.

## Inputs
- `mode` (COMBO): `std` or `pro`
- `aspect_ratio` (COMBO): `1:1`, `9:16`, `16:9`
- `duration` (COMBO): `3` to `15`
- `multi_shots` (BOOLEAN): enables multi-shot mode
- `prompt` (STRING): single-shot prompt
- `shots_text` (STRING, optional): multi-shot lines:
  - `shot_label | duration | prompt`
  - duration accepts `4` or `4 seconds`
- `first_frame` (IMAGE, optional): start frame
- `last_frame` (IMAGE, optional): end frame (single-shot only)
- `sound` (BOOLEAN, optional): single-shot only
- `element` (KIE_ELEMENT, optional): one element
- `elements` (KIE_ELEMENTS, optional): batched elements
- `payload_data` (KIE_KLING3_REQUEST, optional): prebuilt validated payload from preflight; when connected, this overrides direct field inputs
- `log` (BOOLEAN, optional)

## Rules
- `multi_shots=true`:
  - `last_frame` is invalid
  - `sound` is invalid
  - shot durations are summed automatically and sent as the final payload duration
- If both start and end frames are provided, aspect ratio is auto-adapted from frames.
- `@element_name` references in prompt(s) must match provided elements.
- If prompts use `@element_name`, connect `first_frame` (KIE requires image_urls for element-referenced prompts).
- If no frames and no elements are used, the node runs as text-to-video.
- Multi-shot total duration must stay within `3..15` seconds.

## Prompt vs Multi-Prompt
- Single-shot (`multi_shots=false`): use `prompt`.
- Multi-shot (`multi_shots=true`): use `shots_text` only.
- `shots_text` format:
  - `shot_label | duration | prompt`
  - duration accepts `4` or `4 seconds`
- Example:
  - `shot 1 | 4 seconds | A woman exits a spaceship with @dog`
  - `shot 2 | 3 seconds | Medium tracking shot of @dog running`
  - `shot 3 | 3 seconds | Emotional close-up of @dog and @old_woman`

## Element Naming and References
- Define elements upstream with `KIE Kling Elements`.
- Batch them with `KIE Kling Elements Batch`.
- Reference in prompt with `@element_name`.
- Allowed element names: letters, numbers, `_`, `-` only.
- Spaces in element names are invalid.

## Scenario Matrix
- Single-shot with first frame only:
  - Valid
- Single-shot with first + last frame:
  - Valid
  - `aspect_ratio` omitted in payload (auto-adapt from frames)
- Multi-shot with first frame only:
  - Valid
- Multi-shot with last frame connected:
  - Invalid
- Multi-shot with sound enabled:
  - Invalid
- Prompt references `@element` but elements missing:
  - Invalid
- Prompt references `@element` but first frame missing:
  - Invalid
- No frames, no elements:
  - Valid text-to-video

## Cost note
- Kling 3.0 usage cost is tied to generated duration.
- In multi-shot mode, cost follows the computed total shot duration (max 15s).

## Output
- `VIDEO`: SaveVideo-compatible ComfyUI video output.
