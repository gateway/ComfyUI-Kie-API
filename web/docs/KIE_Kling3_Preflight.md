# KIE Kling 3.0 Preflight

Validate Kling 3.0 inputs and build the exact payload JSON without submitting a generation task.

> Status: Experimental support node for Kling 3.0 development.

## Purpose
- Catch wiring and formatting errors before expensive generation.
- Preview exactly what would be sent to:
  - `POST https://api.kie.ai/api/v1/jobs/createTask`

## Inputs
- Same inputs as `KIE Kling 3.0 (Video)`.

## Outputs
- `payload_data` (KIE_KLING3_REQUEST): validated payload object for direct chaining into `KIE Kling 3.0 (Video)`.
- `payload_json` (STRING): exact request payload after validation and upload URL resolution.
- `notes` (STRING): validation summary with detected settings and status.

## Notes
- This node still uploads required input media to produce valid URLs in payload.
- In multi-shot mode, duration is auto-calculated from shot durations.
- `notes` returns a `VALID` summary when checks pass, including:
  - mode, single/multi-shot status, resolved duration
  - frame count and aspect-ratio handling
  - element count and names
  - shot count (multi-shot) or sound status (single-shot)
