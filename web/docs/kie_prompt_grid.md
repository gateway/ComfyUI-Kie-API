# KIE Parse Prompt Grid JSON (1..9)

Parse LLM JSON containing up to 9 prompts and expose each prompt as a separate string output.

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

- **p1..p9**
  Each prompt as a separate STRING output. Missing entries are empty strings.

- **count**
  Number of prompts successfully parsed.

- **prompts_list**
  Raw list of prompts for future automation or batching (not stringified).

---

## Grid wiring tips

- **2x2 grid**: Use p1..p4.
- **3x3 grid**: Use p1..p9.

Feed each prompt into the corresponding downstream node inputs.

---

## Notes

- Empty strings are discarded.
- Keyed objects are ordered by numeric suffix.
- If parsing fails or yields zero prompts, the node raises an error unless strict is false and a default prompt is provided.
- The debug toggle can be enabled to print parsing diagnostics (payload type, matched indices).
