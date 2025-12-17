# ComfyUI KIE API Integration

This repository sets up the groundwork for integrating the KIE Nano Banana Pro API into ComfyUI custom nodes.

## Installation
- Place this repository inside your `ComfyUI/custom_nodes` directory (clone or copy).
- Restart ComfyUI so it discovers the node package.

## API Key Setup
- Copy `config/kie_key.example.txt` to `config/kie_key.txt`.
- Paste your KIE API key into `config/kie_key.txt` (this file is gitignored).
- Keep the key file alongside the repo so future nodes can read it.

## Future Nodes
- Placeholder for upcoming node descriptions and usage once implementation lands


## Working Notes

- Custom ComfyUI nodes for KIE / Nano Banana Pro.
- Repo is structured as a Python package (relative imports required).
- All API endpoints and enums are pinned in docs/ — do not guess values.
- Image uploads capped at 8 references per request.
- Credit checks are advisory (fail only when credits <= 0).
- Logging is console-based (toggle via node input).
.
