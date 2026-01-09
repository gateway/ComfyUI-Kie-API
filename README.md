# ComfyUI KIE API Integration

ComfyUI custom nodes for the KIE API (image and video generation).

## Installation
- Clone or copy this repository into `ComfyUI/custom_nodes/ComfyUI-Kie-API`.
- Restart ComfyUI so it discovers the node package.

## API Key Setup
- Copy `config/kie_key.example.txt` to `config/kie_key.txt`.
- Paste your KIE API key into `config/kie_key.txt` (this file is gitignored).
- Keep the key file alongside the repo so future nodes can read it.

## Nodes
- KIE Get Remaining Credits
- KIE Nano Banana Pro (Image)
- KIE Seedream 4.5 Text-To-Image
- KIE Seedream 4.5 Edit
- KIE Seedance V1 Pro Fast (I2V)
- KIE Seedance 1.5 Pro (I2V/T2V)
- KIE Kling 2.6 (I2V/T2V)
- KIE Kling 2.6 (T2V)
- KIE Kling 2.6 Motion-Control (I2V)
- KIE Grid Slice
- KIE Parse Prompt Grid JSON (1..9)

## Usage
- Drop a KIE node into your ComfyUI workflow and connect inputs.
- For video outputs, connect the VIDEO output to the SaveVideo node.
- Public node documentation lives in `web/docs`.

## Documentation
- See `web/docs` for per-node details and parameter lists.
- Development-only notes and tooling configs are not shipped in this repo.
