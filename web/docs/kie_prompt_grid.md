# KIE Parse Prompt Grid JSON (1..9)

Parse LLM JSON containing up to 9 prompts and expose each prompt as a separate string output.

This node requires a wired STRING input for `json_text`. It does not provide a manual JSON textbox.

---

## Inputs

- `json_text` (STRING, required): Wired JSON text from an upstream node.
- `max_items` (INT, optional): Maximum prompts to return (1..9).
- `strict` (BOOLEAN, optional): Fail hard when parse fails or prompts are missing.
- `default_prompt` (STRING, optional): Fallback when strict mode is off.
- `debug` (BOOLEAN, optional): Enable parser diagnostics in console.

---

## Example JSON inputs

Array format:
```
[
  "Prompt 1",
  "Prompt 2",
  "Prompt 3",
  "Prompt 4"
]
```

Object format (prompts array):
```
{
  "prompts": ["Prompt 1", "Prompt 2"]
}
```

Object format (keyed prompts):
```
{
  "p1": "Prompt 1",
  "prompt2": "Prompt 2",
  "Prompt 3": "Prompt 3",
  "4": "Prompt 4"
}
```

Object format (underscore keys):
```
{
  "prompt_1": "Prompt 1",
  "prompt_2": "Prompt 2",
  "prompt_3": "Prompt 3"
}
```

---

## Outputs

- **prompt 1..prompt 9**
  Each prompt as a separate STRING output. Missing entries are empty strings.

- **count**
  Number of prompts successfully parsed.

- **prompts_list**
  Raw list of prompts for future automation or batching (not stringified).

- **prompts_list_seq**
  Prompts as a ComfyUI list output (OUTPUT_IS_LIST) for sequential downstream processing.

---

## Grid wiring tips

- **2x2 grid**: Use prompt 1..prompt 4.
- **3x3 grid**: Use prompt 1..prompt 9.

Feed each prompt into the corresponding downstream node inputs.

---

## Notes

- Empty strings are discarded.
- Keyed objects are ordered by numeric suffix.
- If parsing fails or yields zero prompts, the node raises an error unless strict is false and a default prompt is provided.
- The debug toggle can be enabled to print parsing diagnostics (payload type, matched indices).
