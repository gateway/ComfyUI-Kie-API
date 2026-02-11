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
- `payload_json` (STRING): exact request payload after validation and upload URL resolution.
- `notes` (STRING): confirms this node does not call `createTask`.

## Notes
- This node still uploads required input media to produce valid URLs in payload.
- In multi-shot mode, duration is auto-calculated from shot durations.
