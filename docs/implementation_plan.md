# ComfyUI Node + Helper Separation Plan

## Goals
- Keep model-specific API logic in helpers (`kie_api/*`).
- Keep ComfyUI node definitions in `nodes.py` (or a future `nodes/` package).
- Ensure every node relies on helpers instead of re-implementing API calls.
- Document best practices and track follow-up fixes.

## Current Nodes (as of Jan 30, 2026)
Image:
- Nano Banana Pro (image)
- Seedream 4.5 (text-to-image)
- Seedream 4.5 (edit)

Video:
- Kling 2.5 I2V Pro
- Kling 2.6 I2V
- Kling 2.6 T2V
- Kling 2.6 Motion I2V
- Seedance V1 Pro Fast I2V
- Seedance 1.5 Pro I2V/T2V

Helpers:
- auth, credits, http, log, jobs, results
- upload, images, video, validation, grid, prompt_lists
- model-specific helpers: nanobanana, seedream45_t2i, seedream45_edit, seedance*, kling*

## Best Practices Implementation (Current Standard)
1) **Nodes are thin wrappers.**
   - Node `generate()` methods delegate to helper functions (`run_*`).
   - Node I/O uses ComfyUI types (`IMAGE`, `VIDEO`, `STRING`, `INT`, `BOOLEAN`).

2) **Helpers encapsulate the full job lifecycle.**
   - Validation → upload → create task → poll → download/decode → credits logging.
   - Shared behavior is already centralized in `jobs.py`, `upload.py`, `images.py`, `video.py`, `validation.py`.

3) **Consistent error handling.**
   - `TransientKieError` signals retryable failures (HTTP 429 or 5xx, transient task failure states).
   - Non-retry errors raise `RuntimeError` with clear messages.

4) **Logging is centralized and predictable.**
   - `_log()` is used for all progress messages.
   - Nodes expose a `log` flag and pass it through.

5) **Enum inputs are pinned.**
   - ComfyUI node options use COMBOs that map to pinned server enums (`duration`, `aspect_ratio`, etc.).

6) **Helpers own logic; nodes own UI.**
   - No API calls, uploads, or polling logic inside nodes.
   - Nodes should only translate ComfyUI inputs → helper inputs and return helper outputs.

7) **Docs reflect actual behavior.**
   - Node docs in `web/docs/` mirror the helper inputs/outputs and current defaults.
   - HELP text and `INPUT_TYPES` must match.

## Things To Review / Fix (Cleanup Targets)
1) **Duplicate `createTask` logic across helpers.**
   - `nanobanana.py`, `kling25_i2v.py`, `kling26_i2v.py`, `kling26_t2v.py`, `kling26motion_i2v.py`,
     `seedance*`, `seedream*` all implement request + error handling for `createTask`.
   - Candidate: move to `jobs.py` or a `requests.py` helper for shared API calls.

2) **Duplicate image upload + validation patterns.**
   - Each model re-validates image tensor shapes, slices batches, and uploads via `_upload_image`.
   - Candidate: a shared helper (e.g. `_upload_first_image`, `_upload_images_limit`).

3) **Node inputs do not expose all documented parameters.**
   - Several node HELP blocks mention `poll_interval_s`, `timeout_s`, and retry settings,
     but these are not exposed in `INPUT_TYPES`.
   - Decide whether to:
     - expose them via `INPUT_TYPES`, or
     - remove from HELP to avoid confusion.

4) **Model docs vs helper docs drift risk.**
   - `web/docs/` contains node pages; helper behavior lives in `kie_api/*`.
   - Add a short helper summary section per model doc or generate them from helpers.

5) **Category naming consistency.**
   - Some helpers appear as nodes in `kie/helpers` (grid, prompt parsing), while others are `kie/api`.
   - Clarify if helper nodes should live under a dedicated category and be separated from API nodes in UI.

## Cleanup Task List (Initial)
### 2) Normalize helper APIs (createTask + upload + validation)
- Extract a shared `create_task()` helper (or move into `jobs.py`) to remove per-model duplication.
- Add shared helpers for common upload patterns:
  - upload first image
  - upload optional tail image
  - upload list of images with a max limit
- Consolidate image shape validation helpers (single image vs batch) into `validation.py`.

### 3) Align node HELP with `INPUT_TYPES`
- Audit each node in `nodes.py` for:
  - missing inputs referenced in HELP
  - defaults or ranges that differ between HELP and `INPUT_TYPES`
- Either expose these inputs or remove them from HELP to avoid mismatch.

### 4) Keep docs in sync with helpers
- For each model in `web/docs/`, add a short “Helper behavior” section:
  - validation rules
  - retry behavior
  - polling defaults
  - output format
- Add a checklist to update docs when helper defaults change.

## Next Steps (if approved)
1) Create a dedicated “Best Practices + Implementation Checklist” doc for adding new models.
2) Start Cleanup Task List item 3 (HELP vs INPUT_TYPES) as the first low-hanging task.
3) After cleanup item 3, draft a new node using the standard pattern.
