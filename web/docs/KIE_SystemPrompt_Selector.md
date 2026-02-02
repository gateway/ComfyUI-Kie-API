## KIE System Prompt Selector

Combine a user prompt with a system prompt template stored in `prompts/images` or `prompts/videos`.

### Inputs
- **user_prompt** (STRING, required): The user prompt text.
- **system_template** (COMBO, required): Template name pulled from `prompts/images/*.txt` and `prompts/videos/*.txt`.

### Outputs
- **STRING**: Combined prompt (system + user).

### Template format
Each `.txt` file in `prompts/images/` or `prompts/videos/` must include:
```
name: <dropdown label>
system prompt below
<template body with optional {user_prompt} placeholder>
```

### Behavior
- If `{user_prompt}` is present, it is replaced with the user prompt.
- If not present, the user prompt is appended to the end of the template.
- Files missing `name:` or `system prompt below` are ignored.
