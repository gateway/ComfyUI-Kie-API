# System Prompt Templates

Put your system prompt templates in subfolders as `.txt` files:
- Image prompts go in `prompts/images/`
- Video prompts go in `prompts/videos/`

Each template file must include:
- A `name:` line for the dropdown label
- A `system prompt below` line marking the start of the template body
- Optional `{user_prompt}` placeholder for insertion

Create a new prompt by placing a `.txt` file in the appropriate folder, adding the `name:` line at the top, then `system prompt below`, then your full system prompt text.

Example:
```
name: Character Consistency v1
system prompt below
You are a helpful assistant. Always preserve the character's identity.
When the user says: {user_prompt}
Return concise instructions for image generation.
```

Notes:
- This README is ignored by the node.
- If `{user_prompt}` is missing, the user prompt is appended at the end.
