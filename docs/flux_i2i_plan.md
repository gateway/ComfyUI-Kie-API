# Flux 2 I2I Nodes — Plan

## Spec scan (source of truth)
- `_internal/docs/KIE_API_FLUX-2-PRO-I2I_SPEC.md`
- `_internal/docs/KIE_AI-FLUX-2-FLEX-I2I_SPEC.MD`

## Field comparison (Pro vs Flex)
Same fields in both specs:
- `model` (string; only value differs)
- `input.input_urls` (required, array URL, 1–8 images)
- `input.prompt` (required, 3–5000 chars)
- `input.aspect_ratio` (required enum)
- `input.resolution` (required enum)
- `callBackUrl` (optional)

Enumerations (identical):
- `aspect_ratio`: 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3, auto
- `resolution`: 1K, 2K

Conclusion: inputs/outputs are identical; only `model` differs.

## Node architecture decision
We can implement a **single node** with a `model` dropdown:
- `flux-2/pro-image-to-image`
- `flux-2/flex-image-to-image`

Conditions satisfied:
- All other parameters are the same in both specs.
- Output type is the same (IMAGE).

## Helper vs node split
Helper:
- `kie_api/flux2_i2i.py` (new)
- Accept `model` as a required argument.
- Handle upload, createTask, poll, download, decode.

Node:
- `KIE_Flux2_I2I` in `nodes.py`
- `model` dropdown + inputs from spec
- Calls `run_flux2_i2i(...)`

Docs:
- `web/docs/KIE_Flux2_I2I.md` (new)

## Open questions (confirm before code)
1) Should we allow 1–8 images (batch) or force 1 image?
2) Do you want `model` in node name or just in a dropdown?
