# KIE Seedream 4.5 Edit — Multi-Image Support Task List

Goal: allow the Seedream45_Edit node/helper to accept and upload up to 14 input images, then pass all uploaded URLs to `input.image_urls`.

## Context (current behavior)
- Helper: `kie_api/seedream45_edit.py` uploads only the first image in the batch.
- Node: `nodes.py` HELP text explicitly says "first image used".
- Spec: `_internal/docs/KIE_API_SEEDREAM_45_EDIT_SPEC.md` lists `input.image_urls` but does not specify a max count.
- Multi-image patterns to mirror: `kie_api/flux2_i2i.py` and `kie_api/nanobanana.py`.

## Open question (must confirm before coding)
- Confirm the server-side max image count for Seedream 4.5 Edit (user believes 14). If confirmed, update the spec doc to include the max.

## Phase 1 — Spec/requirements alignment
- [ ] Confirm max image count with KIE docs or internal source.
- [ ] Update `_internal/docs/KIE_API_SEEDREAM_45_EDIT_SPEC.md` to include max count (1..14) once confirmed.

## Phase 2 — Helper changes (seedream45_edit.py)
- [ ] Add `MAX_IMAGE_COUNT = 14` (or confirmed value).
- [ ] Update `_validate_image_input()` to keep shape checks; do not fail on batch size > 1.
- [ ] Upload up to `MAX_IMAGE_COUNT` images using the pattern in `flux2_i2i.py`:
  - log when more than max provided
  - iterate through `min(total_images, MAX_IMAGE_COUNT)`
  - build `image_urls` list from uploads
- [ ] Update payload to use `image_urls` list (instead of a single URL).
- [ ] Log how many URLs are sent to `createTask` for traceability.

## Phase 3 — Node wrapper and docs
- [ ] Update `nodes.py` HELP text for `KIE_Seedream45_Edit` to reflect up to 14 images and that all provided images are uploaded (up to the cap).
- [ ] Update `web/docs/KIE_Seedream45_Edit.md` with correct inputs/outputs and helper behavior (upload cap, truncation behavior).

## Phase 4 — Validation
- [ ] Run `python3 -m py_compile nodes.py kie_api/seedream45_edit.py`.
- [ ] Minimal manual test: pass a batch of 2+ images and confirm multiple uploads + task creation includes multiple URLs.

## Acceptance criteria
- Helper uploads up to 14 images and sends all URLs in `input.image_urls`.
- If more than 14 images are supplied, the helper logs a truncation message and uses only the first 14.
- Node HELP and web docs clearly describe the multi-image behavior.
