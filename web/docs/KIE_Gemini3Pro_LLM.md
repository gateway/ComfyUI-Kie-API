# KIE Gemini 3 Pro (LLM) [Experimental]

Generate text using Gemini 3 Pro. This node is experimental.

## Inputs
- **prompt** (STRING, required): Text prompt. Used if `messages_json` is empty.
- **messages_json** (STRING, optional): JSON array of message objects (overrides `prompt`).
- **stream** (BOOLEAN, optional): Stream responses via SSE. Output is returned after completion.
- **include_thoughts** (BOOLEAN, optional): Include reasoning content.
- **reasoning_effort** (COMBO, optional): `low`, `high`
- **tools_json** (STRING, optional): JSON array of tool definitions. Mutually exclusive with `response_format_json`.
- **response_format_json** (STRING, optional): JSON schema output format. Mutually exclusive with `tools_json`.
- **log** (BOOLEAN, optional): Enable console logging.

## Outputs
- **STRING**: Assistant response text.
- **STRING**: Reasoning text (empty if include_thoughts is false).
- **STRING**: Raw JSON from the last response chunk.

## Helper behavior
- Validates `reasoning_effort`.
- Enforces mutual exclusivity for tools vs response_format.
- If `messages_json` is provided, it is used as the message array.
