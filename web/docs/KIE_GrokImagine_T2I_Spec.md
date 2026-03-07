# KIE Grok Imagine (T2I) API Spec

## Status
Reference spec for the implemented Grok Imagine text-to-image node. See [`KIE_GrokImagine_T2I.md`](KIE_GrokImagine_T2I.md) for the ComfyUI node surface.

## Endpoint
- Method: `POST`
- Path: `/api/v1/jobs/createTask`
- Base URL: `https://api.kie.ai`
- Model: `grok-imagine/text-to-image`

## Request Body
```json
{
  "model": "grok-imagine/text-to-image",
  "callBackUrl": "https://your-domain.com/api/callback",
  "input": {
    "prompt": "Cinematic portrait of a woman sitting by a vinyl record player, retro living room background, soft ambient lighting, warm earthy tones, nostalgic 1970s wardrobe, reflective mood, gentle film grain texture, shallow depth of field, vintage editorial photography style.",
    "aspect_ratio": "3:2"
  }
}
```

## Root Parameters
- `model` (STRING, required): Must be `grok-imagine/text-to-image`.
- `callBackUrl` (STRING, optional): Receives task completion notifications when provided.
- `input` (OBJECT, required): Generation parameters for the model.

## Input Parameters
- `prompt` (STRING, required): Prompt text. Max length: `5000`.
- `aspect_ratio` (STRING, optional): One of `2:3`, `3:2`, `1:1`, `9:16`, `16:9`.

## Success Response
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "task_12345678"
  }
}
```

## Callback Behavior
If `callBackUrl` is present, KIE posts task completion payloads to that URL for both success and failure states.

### Success Callback Fields
- `code`
- `data.completeTime`
- `data.costTime`
- `data.createTime`
- `data.model`
- `data.param`
- `data.resultJson`
- `data.state`
- `data.taskId`
- `data.failCode`
- `data.failMsg`
- `msg`

### Failure Callback Fields
- `code`
- `data.completeTime`
- `data.costTime`
- `data.createTime`
- `data.failCode`
- `data.failMsg`
- `data.model`
- `data.param`
- `data.state`
- `data.taskId`
- `data.resultJson`
- `msg`

## ComfyUI Mapping Notes
Implemented node shape in this repo:
- `prompt`: `STRING` multiline, required.
- `aspect_ratio`: `COMBO`, optional.
- `log`: `BOOLEAN`, optional.
- Outputs:
  - `IMAGE`
  - `task_id` (`STRING`)

Output behavior:
- Download all `resultUrls` and return them as a ComfyUI `IMAGE` batch if the endpoint returns multiple images.
- Also return the `task_id` from task creation so Grok I2V can reference one of the generated images via `task_id + index`.

## Implementation Notes
- `callBackUrl` should stay transport-level and does not need to be exposed in the first ComfyUI node pass.
- This node is a natural upstream source for Grok I2V chaining.
- The docs do not state how many images are returned per task, but Grok I2V expects `task_id + index` against a prior Grok image-generation task, so keeping `task_id` visible is important.
