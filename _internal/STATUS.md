# Internal Status

Last updated: 2026-02-03

## Active Tasks
- [x] Consolidate Gemini LLM nodes into one with model dropdown (2.5/3 Pro/Flash)
- [x] Gate unsupported options by model (reasoning_effort, response_format, google search)
- [x] Update node docs + README to reflect unified Gemini node

## Notes
- 2026-01-31: Gemini LLM node now selects model via dropdown and logs selected model.
- 2026-02-02: Seedream 4.5 Edit updated to accept up to 14 input images.
- 2026-02-02: Added System Prompt Selector helper node with `prompts/images` + `prompts/videos` templates and docs.
- 2026-02-02: Added sample prompt templates and documented template format in `prompts/README.md`.
- 2026-02-02: Removed deprecated publish workflow and bumped package version to 0.1.4.
- 2026-02-03: Refactored shared image validation + createTask helper into `kie_api/validation.py` and `kie_api/jobs.py` (branch `dev/refactor-helpers`).
- 2026-02-03: Added refactor plan doc for phased helper consolidation in `_internal/docs/KIE_API_REFRACTOR_HELPERS.md`.
- 2026-02-03: Updated Suno music nodes to return two audio outputs and two cover images to match API responses.
- 2026-02-03: Updated README and Suno docs to note two-song/two-cover outputs.
