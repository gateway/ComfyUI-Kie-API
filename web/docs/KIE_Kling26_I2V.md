# KIE Kling 2.6 (Video)

## Overview
Generate a short video clip from a single input image plus a text prompt using the Kling 2.6 image-to-video model.

## Inputs
- prompt (STRING, multiline, required): The text prompt for the video.
- images (IMAGE, required): Source image batch; the first image is used.
- duration (COMBO, seconds, default: 5): Video length. Options: 5, 10.
- sound (BOOLEAN, default: false): Include audio in the output video.
- poll_interval_s (FLOAT, seconds, default: 1.0): How often to poll job status.
- timeout_s (INT, seconds, default: 600): Max wait time before timing out.
- log (BOOLEAN, default: true): Enable KIE console logs.
- retry_on_fail (BOOLEAN, default: true): Retry on transient API failures.
- max_retries (INT, default: 2): Number of retry attempts.
- retry_backoff_s (FLOAT, seconds, default: 3.0): Delay between retries.

## Outputs
- video_path (STRING): Local path to the generated video file.

## Examples
Prompt: "A small robot dances on a wooden desk under warm sunlight."
Duration: 5
Sound: false

## Troubleshooting
- Timeouts: Increase timeout_s or reduce duration to 5 seconds.
- Internal error / try later: Enable retries and increase retry_backoff_s.
- Insufficient credits: Check remaining credits and top up your KIE account.
