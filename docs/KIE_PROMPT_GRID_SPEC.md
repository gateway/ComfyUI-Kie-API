KIE Prompt Grid Parser Spec

Node name
- KIE Parse Prompt Grid JSON (1..9)

Inputs
- json_text (STRING, multiline): JSON text from an LLM
- default_prompt (STRING, optional): Fallback prompt when parsing yields no prompts and strict is false
- max_items (INT, optional, default 9): Maximum number of prompts to return (1..9)

Accepted JSON shapes
a) list[str]
   ["Prompt 1", "Prompt 2", "Prompt 3"]

b) {"prompts": list[str]}
   {"prompts": ["Prompt 1", "Prompt 2"]}

c) Object keys like p1..p9 / prompt1.. / "Prompt 1" / numeric "1".."9"
   {
     "p1": "Prompt 1",
     "prompt2": "Prompt 2",
     "Prompt 3": "Prompt 3",
     "4": "Prompt 4"
   }

Outputs
- p1..p9 (STRING): Individual prompts (missing entries are empty strings)
- count (INT): Number of prompts parsed
- prompts_list: Raw list of prompts for future automation

Behavior notes
- Prompts are trimmed and empty strings are dropped.
- Keyed objects are ordered by numeric suffix.
- Parsing failures raise a ValueError unless strict is false and a default_prompt is provided at the node level.
