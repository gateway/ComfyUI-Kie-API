# KIE Seedance 2.0 Preflight

Validate Seedance 2.0 inputs, upload required media, and build the exact createTask payload without submitting a generation task.

> Status: Experimental support node for Seedance 2.0 development.

## Purpose
- Catch scenario wiring errors before expensive video runs.
- Preview the exact payload sent to:
  - `POST https://api.kie.ai/api/v1/jobs/createTask`

## Inputs
- Same inputs as `KIE Seedance 2.0 (Video)`, except there is no `seedance_data` passthrough input.

## Outputs
- `seedance_data` (KIE_SEEDANCE2_REQUEST): validated payload object for direct chaining into `KIE Seedance 2.0 (Video)`.
- `payload_json` (STRING): exact request payload after validation and upload URL resolution.
- `notes` (STRING): validation summary with resolved scenario and media counts.

## Notes
- This node still uploads media so the payload contains real URLs.
- It does not submit `createTask`.
- Current implementation is intentionally scoped to `bytedance/seedance-2`.
- It reports exact payload fields and inferred alias order for references:
  - `@Image1..N` for `reference_image_urls`
  - `@Video1..N` for `reference_video_urls`
  - `@Audio1..N` for `reference_audio_urls`
- Those aliases are based on upload order and are not yet a verified KIE API contract.
- The current `aspect_ratio`, `resolution`, and `duration` options are pinned to the public examples visible in KIE's docs and should be widened only after live API verification.
- KIE's public marketing copy mentions optional lens locking, but the visible request example does not expose a verified request field for it yet.
- The official `Seedance 2.0 Fast` page is not used yet because its published request example is still inconsistent.
