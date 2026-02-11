# KIE Kling 2.5 I2V Pro

## Overview
Generate a short video clip from a prompt and a required first image, with an optional tail image, using the Kling 2.5 Turbo I2V Pro model.

## Inputs
- first_frame (IMAGE, required): Source image batch; the first image is used.
- prompt (STRING, multiline, required): The text prompt for the video.
- last_frame (IMAGE, optional): Optional tail frame; the first image is used if provided.
- negative_prompt (STRING, multiline, optional): Optional negative prompt.
- duration (COMBO, seconds, default: 5): Video length. Options: 5, 10.
- cfg_scale (FLOAT, default: 0.5): Guidance scale from 0.0 to 1.0.
- log (BOOLEAN, default: true): Enable KIE console logs.

## Outputs
- video (VIDEO): ComfyUI video output referencing a temporary .mp4 file.

## Troubleshooting
- If a job stalls or fails, check https://kie.ai/logs.
- This node uses internal defaults for polling/retries/timeouts (not exposed in the UI).
