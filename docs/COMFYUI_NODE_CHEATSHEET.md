# ComfyUI Node Cheatsheet
- IMAGE tensor: torch.Tensor [B,H,W,C], RGB, float [0..1]
- Nodes must define INPUT_TYPES, RETURN_TYPES, FUNCTION, CATEGORY
- Must register NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS
