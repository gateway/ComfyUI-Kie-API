# Building ComfyUI Nodes From KIE API Specs

This is the ground-truth process for turning a pinned KIE API spec into:
- a helper (model runner) in `kie_api/`
- a ComfyUI node wrapper in `nodes.py`
- a matching user-facing doc in `web/docs/`

## Source Material (What We Actually Use)
Primary inputs:
- `_internal/docs/KIE_API_*_SPEC.md` and other spec files in `_internal/docs/`
- `_internal/docs/COMFYUI_NODE_CHEATSHEET.md`
- `_internal/docs/REPO_RULES.md`
- Existing node + helper implementations (`nodes.py`, `kie_api/*.py`)

Note: There is no `codecs/` folder in this repo. If one appears later, add it to this list.

## Non-Negotiable Rules (Do Not Hallucinate)
- Never invent fields or options that are not in a spec.
- If a spec is incomplete or ambiguous, stop and request clarification.
- The helper owns API logic. The node is a thin wrapper only.
- ComfyUI image tensors are **BHWC float32** in **[0..1]**.
- Video outputs must remain compatible with ComfyUI `SaveVideo`.

## Step 1: Parse the Spec (Pin the Facts)
From the spec file, extract these fields exactly:
- **Model name** (string used in the payload `model`)
- **Input fields** (required vs optional)
- **Allowed options** (enumerations for combos)
- **Input constraints** (max lengths, valid ranges, max count)
- **Response shape** (task id, result URLs, failure fields)

If you cannot find a field in the spec, do not add it to the node.

## Step 2: Decide Helper vs Node Responsibilities
Helpers (model runners) MUST do:
- prompt validation (length/range)
- image/video upload (if input URLs are required)
- task creation and polling
- result parsing and download/decoding
- logging + credit logging

Nodes MUST do:
- define ComfyUI inputs/outputs
- call exactly one helper function
- return the helper output without modification

## Step 3: Map Spec Inputs to ComfyUI Inputs
Use these mapping rules (always prefer existing patterns):

Spec field type -> ComfyUI type:
- string prompt -> `STRING` (multiline)
- boolean -> `BOOLEAN`
- number -> `FLOAT` (with min/max/step if in spec)
- integer -> `INT` (with min/max if in spec)
- enum -> `COMBO` with the exact options list
- image URL(s) -> `IMAGE` (ComfyUI tensors), then upload in helper
- video URL(s) -> `VIDEO`, then upload in helper

Required vs optional:
- Spec **required** -> `required` section of `INPUT_TYPES`
- Spec **optional** -> `optional` section of `INPUT_TYPES`

Image and video rules:
- If spec allows 1..N images, accept a batch `IMAGE` input and enforce max N.
- If spec allows optional image list, permit `images=None` and skip upload.
- Video inputs are passed through the existing video helpers.

## Step 4: Implement the Helper (Model Runner)
Location: `kie_api/<model>.py`

Required responsibilities:
1) Validate inputs
2) Upload any images/videos (convert tensors to bytes)
3) Create task (`createTask`)
4) Poll until completion (`recordInfo`)
5) Parse result URLs
6) Download output and convert to ComfyUI types

Existing helpers to reuse:
- `kie_api/auth.py` (`_load_api_key`)
- `kie_api/jobs.py` (`_poll_task_until_complete`)
- `kie_api/upload.py` (image/video upload + conversions)
- `kie_api/images.py` (image download + tensor decode)
- `kie_api/video.py` (video download + SaveVideo-compatible output)
- `kie_api/results.py` (result URL extraction)
- `kie_api/validation.py` (prompt validation)
- `kie_api/log.py` (logging)
- `kie_api/credits.py` (credits logging)

Helper output contract:
- Image models return `torch.Tensor` with shape [B, H, W, C], float32, 0..1
- Video models return a SaveVideo-compatible object (match existing video nodes)

## Step 5: Implement the Node Wrapper
Location: `nodes.py`

Requirements:
- Keep node `generate()` minimal: just call helper and return results.
- `INPUT_TYPES`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `CATEGORY` are required.
- `HELP` must match the actual node inputs and defaults.
- Expose enums as `COMBO` options exactly as listed in the spec.
- If spec includes optional inputs, include them under `optional`.

## Step 6: Register the Node
Ensure:
- The node class is imported in `nodes.py`
- It appears in `NODE_CLASS_MAPPINGS`
- It has a name in `NODE_DISPLAY_NAME_MAPPINGS`

## Step 7: Document the Node (web/docs)
Create or update `web/docs/<NodeName>.md`:
- Match the exact ComfyUI inputs and outputs
- Include defaults and enums
- Add a brief “Helper behavior” summary:
  - validation rules
  - polling defaults
  - retry behavior (if any)

## Helper/Node Consistency Checklist
Before declaring done:
- Node HELP matches INPUT_TYPES (no hidden inputs).
- Helper validates all required fields and enum options.
- Spec-required inputs are not optional in the node.
- All options in the spec are represented as COMBOs.
- Output type is correct (IMAGE or VIDEO).

## Spec-to-Node Quick Example (Image-to-Image)
Spec fields:
- model: "flux-2/pro-image-to-image"
- input.input_urls (required, 1..8)
- input.prompt (required, max 5000)
- input.aspect_ratio (required enum)
- input.resolution (required enum)

ComfyUI node inputs:
- `images: IMAGE` (required)
- `prompt: STRING` (required)
- `aspect_ratio: COMBO` (required)
- `resolution: COMBO` (required)
- `log: BOOLEAN` (optional, local-only)

Helper responsibilities:
- Validate prompt length
- Validate `images` tensor shape and count (max 8)
- Upload images to URLs
- Build payload with `input_urls`
- Create task + poll
- Download result URL and decode to tensor

## When Specs Are Incomplete
If a spec:
- omits an option list
- lacks a max length/range
- conflicts with existing helper behavior

Then:
1) Do not guess defaults.
2) Add a TODO in the spec doc.
3) Ask for clarification or source doc before coding.
