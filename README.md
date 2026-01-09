# ComfyUI KIE API Nodes

## Project overview
A set of ComfyUI custom nodes that connect to the Kie.ai API for image and video generation workflows.

## Why this exists
ComfyUI users often need consistent, API-backed nodes that map directly to model capabilities and work reliably in production workflows. This pack focuses on clear inputs, predictable outputs, and practical integration.

## What’s included
- Image generation nodes
- Image-to-video and text-to-video nodes
- Utility helpers for grid slicing and prompt parsing

Node-specific documentation is available in `web/docs`.

## Available Nodes

This node pack currently includes the following nodes:

### Generation Nodes

- **NanoBanana Image**
  - Image generation node using the Googles Nano Banana Pro model via the Kie.ai API.

- **Seedream Text-to-Image / Edit**
  - Text-to-image and image-editing node for Seedream models.
  - Supports prompt-based generation and edits.

- **Kling 2.6 Image-to-Video**
  - Generates video from a single input image.
  - Uses the Kling 2.6 image-to-video model.

- **Kling 2.6 Motion-Control Image-to-Video**
  - Image-to-video generation with additional motion control parameters.
  - Designed for more directed camera and motion behavior.

- **Kling 2.6 Text-to-Video**
  - Generates video directly from a text prompt.
  - Supports aspect ratio, duration, and sound options as exposed by the API.

### Utility / Helper Nodes

- **GridSlice**
  - Splits a grid image (such as 2×2 or 3×3) into individual images for downstream processing.

- **Prompt Grid JSON Parser**
  - Parses structured JSON output (for example, from an LLM) into individual prompt outputs.
  - Designed for multi-image and storyboard-style workflows.

Each node has its own documentation page under `web/docs/` with detailed inputs, outputs, and usage examples.

## About Kie.ai
Kie.ai is a unified API and model marketplace for image, video, and audio generation. This project is community-maintained and not affiliated with Kie.ai. Learn more at https://kie.ai/.

## Credits and usage
Kie.ai uses a credit-based model for requests. There is no subscription requirement, and pay-as-you-go usage is supported.

## Debugging and job visibility
You can review request history and results at https://kie.ai/logs.

## Disclaimer
This software is provided as-is. You are responsible for managing your own API usage and credits.

## License
MIT License is recommended. See `LICENSE` for details.
