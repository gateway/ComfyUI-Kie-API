# KIE Kling 2.6 Motion-Control (I2V)

## Overview
Generate a short video clip from a prompt, a single reference image, and a motion reference video using the Kling 2.6 motion-control model.

## Inputs
- prompt (STRING, multiline, required): The text prompt for the video.
- images (IMAGE, required): Source image batch; the first image is used.
- video (VIDEO, required): Motion reference video clip used for motion control.
- character_orientation (COMBO, default: video): Match character orientation to the image or the video. Options: image, video.
- mode (COMBO, default: 720p): Output resolution. Options: 720p, 1080p.
- poll_interval_s (FLOAT, seconds, default: 10.0): How often to poll job status.
- timeout_s (INT, seconds, default: 900): Max wait time before timing out.
- log (BOOLEAN, default: true): Enable KIE console logs.
- retry_on_fail (BOOLEAN, default: true): Retry on transient API failures.
- max_retries (INT, default: 2): Number of retry attempts.
- retry_backoff_s (FLOAT, seconds, default: 3.0): Delay between retries.

## Outputs
- video (VIDEO): ComfyUI VIDEO output referencing a temporary .mp4 file.

## Examples
Prompt: "The character dances in sync with the reference motion video."
Character orientation: video
Mode: 720p

## Troubleshooting
- Timeouts: Increase timeout_s or use a shorter motion reference clip.
- Internal error / try later: Enable retries and increase retry_backoff_s.
- Insufficient credits: Check remaining credits and top up your KIE account.
