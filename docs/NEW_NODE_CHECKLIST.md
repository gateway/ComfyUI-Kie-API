✅ The “New KIE Node” Golden Workflow (Save This)
Phase 0 — Clean slate (Terminal)

Always start here.

-- git status

If anything is modified:

-commit it or
-stash it

Never add a new node on a dirty tree.

Phase 1 — Pin the API (VS Code + Codex)

📍 Tool: VS Code Codex

Step 1: Add API spec doc

Create:

-- docs/KIE_API_<MODEL>_SPEC.md

Codex prompt:

Create docs/KIE_API_<MODEL>_SPEC.md pinned to the official KIE documentation.
Include:
- model name
- endpoints
- request payload
- allowed options
- example responses
Do not invent fields.
Show diff before applying.


✔ This becomes the single source of truth
✔ Codex will reference this later

Phase 2 — Implement model runner (VS Code + Codex)

📍 Tool: VS Code Codex

Step 2: Add model file

Create:

kie_api/<model>.py

Codex prompt

Add kie_api/<model>.py following docs/MODEL_IMPLEMENTATION_TEMPLATE.md
and docs/KIE_API_<MODEL>_SPEC.md.

Rules:
- Use shared helpers (auth, jobs, images, credits)
- Do NOT duplicate polling or decoding
- Expose exactly one public function: run_<model>()
- Return ComfyUI IMAGE tensor (BHWC float32 0–1)
Show diff before applying.

✔ No node UI here
✔ Pure API + data logic

Phase 3 — Add ComfyUI node wrapper (VS Code + Codex)

📍 Tool: VS Code Codex

Step 3: Create node class in nodes.py

Node = thin wrapper only.

Codex prompt

Add a new ComfyUI node class KIE_<ModelName> to nodes.py.

Requirements:
- Inputs mirror KIE API fields
- Call run_<model>() only
- Add HELP text using ComfyUI help_page format
- Follow existing node style
Do not restructure the file.
Show diff before applying.


✔ This is where:

dropdowns

inputs

help text live

Phase 4 — REGISTER THE NODE (this is the part people forget)

📍 Tool: VS Code Codex

Step 4: Register the node

Always do this as a separate Codex step.

Codex prompt

Register the new node so it appears in ComfyUI.

Tasks:
1) Ensure the node class is imported in nodes.py
2) Add it to NODE_CLASS_MAPPINGS
3) Add a display name to NODE_DISPLAY_NAME_MAPPINGS
Do not modify other nodes.
Show diff before applying.


✔ If this step is skipped → node does NOT exist
✔ This is the #1 missing step you just hit

Phase 5 — Sanity checks (Terminal)

📍 Tool: Terminal

python3 -m py_compile nodes.py
python3 -m py_compile kie_api/<model>.py


If this fails → fix before committing.

Phase 6 — Commit cleanly

📍 Tool: Terminal

git add nodes.py kie_api/<model>.py docs/KIE_API_<MODEL>_SPEC.md
git commit -m "feat: add <MODEL> node"
git push


One model = one commit.

Phase 7 — Windows ComfyUI test

📍 Tool: Windows

-git pull
-restart ComfyUI
-search node by name
-run minimal test

🔁 TL;DR Cheat Sheet

Every new node:

-📄 Spec doc
-⚙️ Model runner (kie_api/*.py)
-🧱 Node class (nodes.py)
-🔌 Register node in mappings
-❓ Add HELP text
-✅ Compile
-🚀 Commit

Why this works

-Codex is great at isolated tasks
-Registration is always explicit
-MODEL_IMPLEMENTATION_TEMPLATE.md prevents drift
-Help text is never forgotten
-ComfyUI never silently skips your node

Optional power move (later)

When you’re ready, you can add:

docs/NEW_NODE_CHECKLIST.md


and literally paste this workflow in it — Codex can even be told:

“Follow docs/NEW_NODE_CHECKLIST.md exactly.”