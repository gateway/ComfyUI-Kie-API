# KIE Sora 2 Image-To-Video Stable

Generate a short video clip from an image and a prompt using Sora 2 (stable endpoint).

## Inputs
- **image**: Source image batch (first image used)
- **prompt**: Text prompt (required)
- **aspect_ratio**: `portrait` or `landscape`
- **n_frames**: `10` or `15`
- **upload_method**: `s3` or `oss`
- **poll_interval_s**: Interval in seconds between status checks (default: 10.0).
- **timeout_s**: Maximum time in seconds to wait for generation (default: 2000).
- **retry_on_fail**: Whether to automatically retry on transient API errors (default: True).
- **max_retries**: Number of retry attempts (default: 2).
- **retry_backoff_s**: Seconds to wait before retrying (default: 3.0).
- **log**: Enable detailed logging to the ComfyUI console.

## Outputs
- **VIDEO**: The generated video file.
