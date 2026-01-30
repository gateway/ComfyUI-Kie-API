# Flux 2 I2I — Task List

## Phase 0: Agree on scope
- Confirm single node with model dropdown is acceptable.
- Confirm allowed image count (1 vs 1–8).

## Phase 1: Spec-to-helper
- Add `kie_api/flux2_i2i.py`
  - constants: MODEL_OPTIONS, ASPECT_RATIO_OPTIONS, RESOLUTION_OPTIONS
  - validate prompt length (3–5000)
  - validate images tensor shape and count
  - upload images (1..8)
  - createTask + poll + extract result URLs
  - download + decode to tensor

## Phase 2: Node wrapper
- Add class `KIE_Flux2_I2I` to `nodes.py`
- `INPUT_TYPES` reflects spec (plus `model` dropdown, `log`)
- Call `run_flux2_i2i(...)`
- Add HELP text

## Phase 3: Register node
- Import new helper in `nodes.py`
- Add to `NODE_CLASS_MAPPINGS`
- Add to `NODE_DISPLAY_NAME_MAPPINGS`

## Phase 4: Docs
- Add `web/docs/KIE_Flux2_I2I.md`
- Include inputs/outputs + enums + defaults

## Phase 5: Sanity checks
- `python3 -m py_compile nodes.py kie_api/flux2_i2i.py`
