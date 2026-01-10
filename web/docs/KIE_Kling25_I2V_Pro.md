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
- poll_interval_s (FLOAT, seconds, default: 10.0): How often to poll job status.
- timeout_s (INT, seconds, default: 1000): Max wait time before timing out.
- log (BOOLEAN, default: true): Enable KIE console logs.
- retry_on_fail (BOOLEAN, default: true): Retry on transient API failures.
- max_retries (INT, default: 2): Number of retry attempts.
- retry_backoff_s (FLOAT, seconds, default: 3.0): Delay between retries.

## Outputs
- video (VIDEO): ComfyUI video output referencing a temporary .mp4 file.

## Troubleshooting
- If a job stalls or fails, check https://kie.ai/logs.
- Timeouts: Increase timeout_s or use duration 5 seconds.
