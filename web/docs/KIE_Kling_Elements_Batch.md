# KIE Kling Elements Batch

Batch up to 9 `KIE_ELEMENT` payloads into one `KIE_ELEMENTS` payload for the Kling 3.0 node.

## Inputs
- `element_1` to `element_9` (KIE_ELEMENT, optional)

## Rules
- At least one element is required.
- Duplicate element names are rejected.

## Outputs
- `KIE_ELEMENTS`: batched elements payload
- `STRING`: JSON preview of batched elements
