# KIE Sora 2 Characters Pro

Extracts a reusable character from an existing Sora 2 video and registers it as a named @handle.

## Inputs
- **origin_task_id**: taskId of a previously generated Sora 2 video (required)
- **start_time**: Clip start in seconds (required)
- **end_time**: Clip end in seconds. Selected segment must be 1-4 seconds long. (required)
- **character_prompt**: Short line describing stable traits. (required)
- **character_user_name**: Globally unique handle for your character. (optional)
- **safety_instruction**: Content boundaries. (optional)
- **poll_interval_s**: Interval in seconds between status checks (default: 10.0).
- **timeout_s**: Maximum time in seconds to wait for generation (default: 2000).
- **retry_on_fail**: Whether to automatically retry on transient API errors (default: True).
- **max_retries**: Number of retry attempts (default: 2).
- **retry_backoff_s**: Seconds to wait before retrying (default: 3.0).
- **log**: Enable detailed logging to the ComfyUI console.

## Outputs
- **character_handle**: The @username for use in downstream prompts (STRING).
