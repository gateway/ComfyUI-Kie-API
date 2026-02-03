# KIE Suno Music (Basic)

Create a Suno music generation task via KIE API. This node keeps inputs minimal and returns two AUDIO outputs + two cover images.

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
- **log** (BOOLEAN): Enable console logging.

## Outputs
- **audio_1** (AUDIO): Generated audio 1.
- **audio_2** (AUDIO): Generated audio 2.
- **data** (STRING): Full API response JSON (formatted).
- **image_1** (IMAGE): Generated cover image 1.
- **image_2** (IMAGE): Generated cover image 2.

## Notes
- Non-custom mode expects **prompt only** (500 chars max); other fields should be empty.
- Custom mode requirements:
  - Instrumental: `style` + `title`
  - Non-instrumental: `style` + `title` + `prompt`
