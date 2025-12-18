# Codex Instructions (PIN): ComfyUI Custom Nodes
Follow these instructions exactly when writing code for this repo.

**For ComfyUI node rules, use docs/COMFY_ORG_CANONICAL_REFERENCES.md.
“**Do not invent tensor shapes; follow the doc.

- Always follow ComfyUI node conventions.
- IMAGE tensors are torch.Tensor [B,H,W,C] float [0..1].
- Read API key from config/kie_key.txt (gitignored).
- Use docs/ as the source of truth
- All KIE endpoints must come from docs/KIE_API_NANOBANANA_SPEC.md. If missing, ask the user.
- No guessing endpoints: “All KIE endpoints must be present in docs/KIE_API_*.md. If missing, ask the user.”
- No guessing enums: “Aspect ratios / resolution / output_format must match pinned enums exactly.”
- No surprise inputs: “Only expose node inputs that exist in pinned spec (plus log, timeout, poll_interval).”.


