# KIE Seedance 2.0 (Video)

Generate Seedance 2.0 videos with either supported KIE model:
- `bytedance/seedance-2-fast`
- `bytedance/seedance-2`

> Status: Experimental development pass.
> Credit Warning: Seedance 2.0 can take several minutes per job. Use `KIE Seedance 2.0 Preflight` first.

## Inputs
- `model` (COMBO, required): `bytedance/seedance-2-fast` or `bytedance/seedance-2`.
- `prompt` (STRING, required): main prompt text.
- `first_frame` (IMAGE, optional): single first frame image.
- `last_frame` (IMAGE, optional): single last frame image. Requires `first_frame`.
- `reference_images` (IMAGE, optional): one or more reference images for multimodal reference mode.
- `reference_video` (VIDEO, optional): one reference video for multimodal reference mode.
- `reference_audio` (AUDIO, optional): one reference audio input for multimodal reference mode.
- `generate_audio` (BOOLEAN, optional): asks KIE to generate audio.
- `return_last_frame` (BOOLEAN, optional): asks KIE to include a last-frame artifact when supported.
- `aspect_ratio` (COMBO, optional): `16:9`, `9:16`, `1:1`.
- `resolution` (COMBO, optional): `480p`, `720p`, `1080p`.
- `duration` (COMBO, optional): `5`, `10`, `15`.
- `web_search` (BOOLEAN, optional): forwards KIE's web-search toggle.
- `seedance_data` (KIE_SEEDANCE2_REQUEST, optional): validated payload from preflight. When connected, this overrides direct field inputs.
- `log` (BOOLEAN, optional): enable helper logging.

## Scenario Rules
- Text-to-video:
  Connect no media inputs.
- First-frame image-to-video:
  Connect `first_frame` only.
- First+last-frame image-to-video:
  Connect `first_frame` and `last_frame`.
- Multimodal reference-to-video:
  Connect any mix of `reference_images`, `reference_video`, and `reference_audio`.
- Hybrid control mode:
  You can combine `first_frame` and `last_frame` with reference media in the same request.
- `last_frame` still requires `first_frame`.

## Reference Ordering
- `first_frame` and `last_frame` become dedicated payload slots:
  - `first_frame_url`
  - `last_frame_url`
- `reference_images` are uploaded in input order and sent as `reference_image_urls`.
- `reference_video` is sent as `reference_video_urls[0]`.
- `reference_audio` is sent as `reference_audio_urls[0]`.
- Current best-working prompt convention is likely:
  - `@Image1..N` for `reference_image_urls`
  - `@Video1..N` for `reference_video_urls`
  - `@Audio1..N` for `reference_audio_urls`
- `first_frame_url` and `last_frame_url` should be treated as temporal controls, not as `@ImageN` aliases.

## Notes
- The selected `model` is passed through directly to KIE. The node does not otherwise change payload behavior between fast and non-fast modes.
- The current `aspect_ratio`, `resolution`, and `duration` option lists are pinned to the public KIE examples used for this implementation pass.
  Widen them only after Windows-side live API verification confirms the accepted enum set.
- Preflight now reports the exact payload fields present plus inferred alias order such as `@Image1`, `@Video1`, and `@Audio1`.
  Those aliases are treated as a likely model convention based on upload order, not a verified API contract.
- Mixed payload shapes have now been validated locally at the transport level:
  - `first_frame_url + last_frame_url`
  - `first_frame_url + last_frame_url + reference_image_urls`
  - `first_frame_url + last_frame_url + reference_image_urls + reference_video_urls + reference_audio_urls`
- The official KIE docs currently show a typo with `reference_video_urls ` including a trailing space in the example payload.
  This node normalizes that field when consuming prebuilt payloads.
- KIE's public marketing copy mentions optional lens locking, but the visible request example does not expose a verified request field for it yet.
  This first pass intentionally leaves that transport field out rather than guessing.
- Fast vs non-fast behavior and billing are controlled by the selected `model` value:
  - `bytedance/seedance-2-fast`
  - `bytedance/seedance-2`
- The rest of the payload shape remains the same across both options in current public KIE docs.
- If KIE returns multiple artifacts, the node selects the video URL and ignores extra artifacts in the ComfyUI output contract.

## Output
- `video` (VIDEO): SaveVideo-compatible ComfyUI video output.
