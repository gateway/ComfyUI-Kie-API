# KIE Grok Imagine (I2I) API Spec

## Status
Reference spec for the implemented Grok Imagine image-to-image node. See [`KIE_GrokImagine_I2I.md`](KIE_GrokImagine_I2I.md) for the ComfyUI node surface.

## Endpoint
- Method: `POST`
- Path: `/api/v1/jobs/createTask`
- Base URL: `https://api.kie.ai`
- Model: `grok-imagine/image-to-image`

## Request Body
```json
{
  "model": "grok-imagine/image-to-image",
  "callBackUrl": "https://your-domain.com/api/callback",
  "input": {
    "prompt": "Recreate the Titanic movie poster with two adorable anthropomorphic cats in the same romantic pose at the bow of the ship.",
    "image_urls": [
      "https://static.aiquickdraw.com/tools/example/1767602105243_0MmMCrwq.png"
    ]
  }
}
```

## Root Parameters
- `model` (STRING, required): Must be `grok-imagine/image-to-image`.
- `callBackUrl` (STRING, optional): Receives task completion notifications when provided.
- `input` (OBJECT, required): Generation parameters for the model.

## Input Parameters
- `prompt` (STRING, optional): Text description of the desired edit/style. Max length: `390000`.
- `image_urls` (ARRAY[URL], required): Single reference image URL. Accepted types: `image/jpeg`, `image/png`, `image/webp`. Max size: `10MB`.

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
- `images`: `IMAGE`, required. Upload the first image only.
- `prompt`: `STRING` multiline, default empty string.
- `log`: `BOOLEAN`, optional.
- Outputs:
  - `IMAGE`
  - `task_id` (`STRING`)

Validation behavior:
- Require at least one input image.
- If multiple ComfyUI images are connected, upload the first image only.

Output behavior:
- Download all `resultUrls` and return them as a ComfyUI `IMAGE` batch if the endpoint returns multiple images.
- Also return the `task_id` from task creation so Grok I2V can reference one of the generated images via `task_id + index`.

## Implementation Notes
- `callBackUrl` should stay transport-level and does not need to be exposed in the first ComfyUI node pass.
- This node is a natural upstream source for Grok I2V chaining.
- The callback examples return image URLs, which matches the endpoint type.
