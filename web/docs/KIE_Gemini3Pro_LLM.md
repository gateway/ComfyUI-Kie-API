# KIE Gemini (LLM) [Experimental]

Generate text using Gemini 2.5/3 (Pro/Flash). This node is experimental.

## Inputs
- **model** (COMBO, required): `gemini-3-pro`, `gemini-3-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`
- **prompt** (STRING, required): Main text prompt. Used when `messages_json` is empty.
- **role** (COMBO, required): Message role for the prompt. Options: `developer`, `system`, `user`, `assistant`, `tool`.
- **images** (IMAGE, optional): One or more images (batch) to include as media content.
- **video** (VIDEO, optional): A single video input to include as media content.
- **audio** (AUDIO, optional): Audio input (WAV/MP3) to include as media content.
- **messages_json** (STRING, optional): Full JSON array of message objects. If provided, it overrides `prompt`, `role`, and media inputs.
- **stream** (BOOLEAN, optional): Use streaming responses (SSE). Output is returned after completion.
- **include_thoughts** (BOOLEAN, optional): When enabled, reasoning content is returned in the reasoning output.
- **reasoning_effort** (COMBO, optional): Controls reasoning depth: `low` or `high`.
- **enable_google_search** (BOOLEAN, optional): Enable the Google Search tool. Mutually exclusive with `response_format_json`.
- **messages_json** (STRING, optional): Full JSON array of message objects. If provided, it overrides `prompt`, `role`, and media inputs.
- **response_format_json** (STRING, optional): JSON schema output format. Mutually exclusive with Google Search (not supported for `gemini-3-flash`).
- **log** (BOOLEAN, optional): Enable console logging for uploads and response status.

## Node UI Reference (What each widget expects)
- **Model (dropdown)**: Select which Gemini model endpoint to call.
- **Prompt (text box)**: A natural language instruction or question. Leave empty only if you provide `messages_json` or media.
- **Role (dropdown)**: Sets the `role` field in the message object (default: `user`).
- **Images (input socket)**: Connect a ComfyUI IMAGE or batch. All images are uploaded and appended to message content.
- **Video (input socket)**: Connect a ComfyUI VIDEO. The video is uploaded and appended to message content.
- **Audio (input socket)**: Connect a ComfyUI AUDIO. The audio is uploaded and appended to message content.
- **Messages JSON (text box)**: Raw JSON array of messages (advanced). Overrides prompt/role/media entirely.
- **Stream (toggle)**: Enables SSE streaming under the hood; output still returns when complete.
- **Include Thoughts (toggle)**: When on, reasoning text is captured and returned in the second output.
- **Reasoning Effort (dropdown)**: `low` is faster, `high` is more thorough.
- **Note**: `reasoning_effort` is ignored for `gemini-2.5-flash` (not supported in the spec).
- **Enable Google Search (toggle)**: Sends the Google Search tool payload to the API.
- **Messages JSON (text box)**: Raw JSON array of messages (advanced).
- **Response Format JSON (text box)**: Raw JSON schema definition (advanced).
- **Log (toggle)**: Emits upload and completion messages to the console.

## Outputs
- **STRING**: Assistant response text.
- **STRING**: Reasoning text (empty if include_thoughts is false).
- **STRING**: Raw JSON from the last response chunk.

## Helper behavior
- Validates `reasoning_effort`.
- Enforces mutual exclusivity for Google Search vs response_format.
- If `messages_json` is provided, it is used as the message array and media inputs are rejected.
- Media inputs are uploaded and added to the message content using the unified `image_url` format.
- `response_format_json` is rejected for `gemini-3-flash`.
