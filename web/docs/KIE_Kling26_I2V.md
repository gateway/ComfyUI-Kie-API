# KIE Kling 2.6 (Video)

## Overview
Generate a short video clip from a single input image plus a text prompt using the Kling 2.6 image-to-video model.

## Inputs
- prompt (STRING, multiline, required): The text prompt for the video.
- images (IMAGE, required): Source image batch; the first image is used.
- duration (COMBO, seconds, default: 5): Video length. Options: 5, 10.
- sound (BOOLEAN, default: false): Include audio in the output video.
- log (BOOLEAN, default: true): Enable KIE console logs.

## Outputs
- video (VIDEO): ComfyUI VIDEO output compatible with SaveVideo.

## Examples
Prompt: "A small robot dances on a wooden desk under warm sunlight."
Duration: 5
Sound: false

## Troubleshooting
- This node uses internal defaults for polling/retries/timeouts (not exposed in the UI).
- If a job takes unusually long or fails, check https://kie.ai/logs.
- Insufficient credits: Check remaining credits and top up your KIE account.
