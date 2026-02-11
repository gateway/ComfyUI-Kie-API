# KIE Kling 2.6 Motion-Control (I2V)

## Overview
Generate a short video clip from a prompt, a single reference image, and a motion reference video using the Kling 2.6 motion-control model.

## Inputs
- prompt (STRING, multiline, required): The text prompt for the video.
- images (IMAGE, required): Source image batch; the first image is used.
- video (VIDEO, required): Motion reference video clip used for motion control.
- character_orientation (COMBO, default: video): Match character orientation to the image or the video. Options: image, video.
- mode (COMBO, default: 720p): Output resolution. Options: 720p, 1080p.
- log (BOOLEAN, default: true): Enable KIE console logs.

## Outputs
- video (VIDEO): ComfyUI VIDEO output referencing a temporary .mp4 file.

## Examples
Prompt: "The character dances in sync with the reference motion video."
Character orientation: video
Mode: 720p

## Troubleshooting
- This node uses internal defaults for polling/retries/timeouts (not exposed in the UI).
- If a job takes unusually long or fails, check https://kie.ai/logs.
- Insufficient credits: Check remaining credits and top up your KIE account.
