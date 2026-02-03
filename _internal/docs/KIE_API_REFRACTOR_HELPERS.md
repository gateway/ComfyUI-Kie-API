# KIE API Helper Refactor Plan

Purpose: keep model wrappers thin and move reusable behavior into shared helpers to reduce drift, simplify maintenance, and lower risk of subtle behavior differences across nodes.

This document is intended to be a living reference so refactors can be done in phases without losing context or expanding scope unintentionally.

## Guiding principles
- Preserve ComfyUI node behavior exactly (logging text, errors, defaults, and API payloads).
- Prefer small, incremental moves into existing helpers.
- Only change one dimension at a time (validation, createTask, uploads, polling, decoding).
- Keep wrapper modules focused on: input validation (by helper), payload construction, and orchestration.

## Scope map (what belongs where)
- **Wrappers (model files)**: model-specific options, payload fields, and UI-level defaults.
- **Helpers (shared)**: input validation, API transport, polling, uploads, decoding, payload templates, constants.

## Phase 1 (Minimal): validation + createTask extraction
Status: **completed in dev branch `dev/refactor-helpers`**

### Changes delivered
1) Shared image tensor validation
- Added helper: `kie_api/validation.py:_validate_image_tensor_batch`
- Replaced local copies in:
  - `kie_api/kling26_i2v.py`
  - `kie_api/kling26motion_i2v.py`
  - `kie_api/seedancev1pro_fast_i2v.py`
  - `kie_api/seedream45_edit.py`

2) Shared createTask helper
- Added helper: `kie_api/jobs.py:_create_task`
- Replaced local createTask copies in:
  - `kie_api/kling26_i2v.py`
  - `kie_api/kling26motion_i2v.py`
  - `kie_api/kling25_i2v.py`
  - `kie_api/seedancev1pro_fast_i2v.py`
  - `kie_api/seedream45_edit.py`
  - `kie_api/kling26_t2v.py` (import now from jobs)

### Risk assessment
- **Likelihood of break**: Low
- **Why**: Logic moved verbatim into shared helpers; wrappers still call with identical inputs; payloads unchanged.
- **Risk surface**: Import paths, missing helpers, or overlooked custom behavior.

### Maintenance cost reduction
- Validation: 4 copies -> 1 helper
- createTask: 5 copies -> 1 helper
- Expected savings: fewer drift bugs when API error handling changes.

## Phase 2 (Moderate): model option validation + enums
Status: **not started**

### Candidate targets
- Seedream 4.5 `_validate_options` (duplicate across `seedream45_edit` and `seedream45_t2i`)
- Common enum lists (durations, resolutions, aspect ratios)

### Suggested helpers
- `kie_api/seedream45.py:validate_seedream45_options`
- `kie_api/constants.py` for enum lists

### Risk assessment
- **Likelihood of break**: Low–Medium
- **Why**: If enums are moved incorrectly or reused across incompatible models, behavior could change.

## Phase 3 (Full): upload + payload + result collection
Status: **not started**

### Candidate targets
- Image upload prep + single-image handling (repeats across I2V models)
- Video upload / coercion patterns in motion-control models
- Standard post-processing: poll -> extract -> download -> decode

### Suggested helpers
- `kie_api/upload.py:prepare_single_image_upload(...)`
- `kie_api/payloads.py:build_kling_i2v_payload(...)`
- `kie_api/runners.py:run_task_and_collect_video(...)`

### Risk assessment
- **Likelihood of break**: Medium
- **Why**: Higher chance of subtle behavior changes (logging, ordering, error messages)
- **Mitigation**: keep wrapper-level logging strings unchanged; add tests or smoke checks with known inputs

## Out of scope (explicitly)
- Any change to node UI defaults or parameter names
- Any change to API payload fields or mapping
- Any change to log messages (unless required for correctness)
- Any behavior change to timeouts, retry logic, or polling intervals

## Verification checklist (ComfyUI nodes)
Smoke test goal: verify refactor didn’t change behavior, logging, or payloads.

- Load workflows using refactored nodes (Kling 2.6 I2V, Kling 2.6 Motion I2V, Seedance V1 Pro Fast I2V, Seedream 4.5 Edit, Kling 2.5 I2V, Kling 2.6 T2V)
- Run each node once with a minimal valid input; confirm job completes and outputs are produced
- Confirm request creation succeeds and polling still completes (no new transient failures)
- Confirm log messages look identical (especially createTask + polling status lines)
- Trigger one invalid input per node (empty prompt or missing image) and confirm error text matches prior behavior
- For Kling 2.5 I2V, verify both `image` only and `image + tail_image` paths still work

## Notes
- Keep this file updated after each refactor phase with: scope, changes, and risk notes.

## Refactor backlog (itemized)
| Item | Status | Maintenance cost if left | Likelihood of break if refactored | Notes |
| --- | --- | --- | --- | --- |
| Shared image tensor validation | Done (Phase 1) | Medium | Low | Verbatim move into `validation.py` |
| Shared createTask helper | Done (Phase 1) | Medium | Low | Verbatim move into `jobs.py` |
| Seedream 4.5 option validation | Not started | Low–Medium | Low–Medium | Shared enums and validation for edit + t2i |
| Shared enum constants | Not started | Low | Low–Medium | Centralize option lists in `constants.py` |
| Shared single-image upload prep | Not started | Medium | Medium | Multiple I2V wrappers duplicate upload + logging |
| Shared payload builders | Not started | Medium | Medium | Risk of subtle field mismatch |
| Shared result runner (poll + download + decode) | Not started | Medium | Medium | Must preserve timing/logging semantics |
