# ComfyUI-Kie-API — Repo Rules (Source of Truth)

This document is the **single source of truth** for how this repo is structured and how changes must be made.

If you are using Codex (terminal or VS Code), **read this file before making changes**.

---

## 1) Non-negotiable rules

- **No manual edits by the user.** All code changes are made via Codex.
- Any change that affects behavior must update **all applicable** areas:
  - `kie_api/*.py` (helpers + model code)
  - `nodes.py` (node registration)
  - `web/docs/*.md` (user-facing node docs)
- Keep code separation clean:
  - **Helpers are generic** (shared utilities, HTTP client, polling, conversions, validation)
  - **Model files are model-specific** (request payload, endpoints, response parsing)
- ComfyUI image tensors are **BHWC float32 in the range 0..1**.
- **VIDEO outputs must be compatible with ComfyUI `SaveVideo`.**
  - Match the repo’s existing return convention used by current video nodes.

---

## 2) Make the repo the source of truth

Add and maintain these docs so Codex stays aligned without relying on chat history:

### A) `docs/MODEL_IMPLEMENTATION_TEMPLATE.md`
Keep this file updated. It must include:

- Required function signature pattern for `run_<model>_*`
- Standard logging pattern: `_log(log, "…")`
- Standard retry behavior (what gets retried, backoff, max attempts)
- Standard return types:
  - **IMAGE**: tensor (BHWC float32 0..1)
  - **VIDEO**: SaveVideo-compatible object (match repo convention)
- “Where to register” checklist:
  - `nodes.py`
  - `NODE_CLASS_MAPPINGS`
  - `NODE_DISPLAY_NAME_MAPPINGS`
  - `web/docs/*.md`

### B) `docs/REPO_RULES.md`
This file (you are reading it) contains the bullet rules and workflow.

---

## 3) Repeatable feature workflow (7-step loop)

Every new feature follows the same loop:

1. Create spec doc (1 file): `docs/KIE_<FEATURE>_SPEC.md`
2. Run Codex to generate/modify code
3. Run `py_compile` on touched modules
4. Restart ComfyUI and confirm node loads
5. Run **1 minimal workflow test**
6. Add/update `web/docs` markdown for the node
7. Commit

This keeps changes small, testable, and debuggable.

---

## 4) Choose one next feature (don’t bundle)

Do changes as small PR-sized chunks. Avoid bundling multiple unrelated changes.

Good next “small chunks” for this repo:

- Video input validation (duration, resolution) using `ffprobe` fallback (optional)
- Upload util supports generic files (image/video) via one function
- GridSlice: move core slicing logic into `kie_api/grid.py` (if not already)
- Node docs for all current nodes using the `web/docs` system
- Standard “Result URL print” for all video nodes

---

## 5) Codex usage pattern (fast + consistent)

Use this every time:

### Terminal
```bash
git checkout -b feature/<name>
codex
```

### Instruction block format (keep it short)
Include:

- **Files to touch**
- **What to add/change**
- **What not to change**
- **Compile command**

Example skeleton:

```text
You are working in ComfyUI-Kie-API.

Hard rules:
- Do not ask the user to manually edit code; make all edits yourself.
- Preserve ComfyUI image tensor contract: BHWC float32 0..1.
- VIDEO outputs must remain compatible with SaveVideo (match existing repo convention).
- Keep helpers generic and model files model-specific.

Files to touch:
- kie_api/<...>.py
- nodes.py
- web/docs/<...>.md
- docs/KIE_<FEATURE>_SPEC.md

Change:
- <describe change precisely>

Do NOT change:
- Existing node return conventions
- Unrelated nodes

After edits, ensure this compiles:
python3 -m py_compile nodes.py kie_api/*.py
```

---

## 6) Debugging without flooding chat

When something breaks, only bring:

- The **stack trace**
- The **one file name + function** mentioned in the error
- The **NODE_CLASS_MAPPINGS** entry (if it’s a load failure)

Do not paste the entire `nodes.py` unless the error is inside `nodes.py`.

---

## 7) Verification (required every change)

### A) Compile check
Run from repo root:

```bash
python3 -m py_compile nodes.py kie_api/*.py
```

### B) Quick ComfyUI checklist

- Start/restart ComfyUI
- Confirm the node appears in the expected category
- Drop node into a minimal graph
- Queue prompt and confirm:
  - No console errors
  - Output type is correct (IMAGE/VIDEO)
  - VIDEO: wire into **SaveVideo** and confirm it saves successfully

---

## Current nodes (reference)

- NanoBanana image
- Seedream t2i/edit
- Kling26 i2v
- Kling26 motion-control i2v
- Seedance i2v
- GridSlice
