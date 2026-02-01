# KIE Suno Music (Advanced)

Create a Suno music generation task via KIE API. This node exposes advanced weights and returns an AUDIO output.

## Inputs
- **title** (STRING, required): Track title (required in custom mode).
- **style** (STRING, required): Style text (required in custom mode, multiline).
- **prompt** (STRING, required): Prompt text (lyrics in custom mode when instrumental is false).
- **custom_mode** (BOOLEAN, required): Enable custom mode.
- **instrumental** (BOOLEAN, required): Instrumental-only mode.
- **model** (COMBO, required): `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5`
Optional:
- **negative_tags** (STRING): Optional.
- **vocal_gender** (COMBO): `male` or `female` (custom mode only).
- **style_weight** (FLOAT): 0..1
- **weirdness_constraint** (FLOAT): 0..1
- **audio_weight** (FLOAT): 0..1
- **log** (BOOLEAN): Enable console logging.

## Outputs
- **audio** (AUDIO): Generated audio.
- **data** (STRING): Full API response JSON (formatted).

## Notes
- Non-custom mode expects **prompt only** (500 chars max); other fields should be empty.
- Custom mode requirements:
  - Instrumental: `style` + `title`
  - Non-instrumental: `style` + `title` + `prompt`
- Polling parses both callback-style (`data.data[].audio_url`) and record-info style (`data.response.sunoData[].audioUrl`) responses.
