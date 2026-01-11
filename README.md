# ComfyUI KIE API Nodes

## Project overview
A set of ComfyUI custom nodes that connect to the Kie.ai API for image and video generation workflows.

## Why this exists
ComfyUI users often need consistent, API-backed nodes that map directly to model capabilities and work reliably in production workflows. This pack focuses on clear inputs, predictable outputs, and practical integration.

### Supporting Development

This project is built for the ComfyUI community and maintained in personal time.

If you find the nodes useful and are already planning to use **Kie.ai**, using the link below is one way to support continued development and improvements. There is no obligation, and everything works the same regardless.

👉 [https://kie.ai](https://kie.ai?ref=e7565cf24a7fad4586341a87eaf21e42)

## What’s included
- Image generation nodes
- Image-to-video and text-to-video nodes
- Utility helpers for grid slicing and prompt parsing

Node-specific documentation is available in `web/docs`.

## API Key Setup

To use these nodes, you must provide your own Kie.ai API key.

**Steps:**
- Open `config/kie_key.example.txt`
- Paste your Kie.ai API key into the file
- Save the file as `kie_key.txt` in the same `config/` directory

**Important:**  
Do **NOT** share your API key or commit it to version control.

## Current Available Nodes

This node pack currently includes the following nodes:

### Generation Nodes

- **Nano Banana Pro Image**
  - Image generation node using the Googles Nano Banana Pro model

- **Seedream Text-to-Image / Edit**
  - Text-to-image and image-editing node for Seedream models.
  - Supports prompt-based generation and edits.

- **Kling 2.6 Image-to-Video**
  - Generates video from a single input image.
  - Uses the Kling 2.6 image-to-video model.

- **Kling 2.5 I2V Pro**
  - Generates video from a required first image and optional tail image.
  - Uses the Kling 2.5 Turbo image-to-video Pro model.

- **Kling 2.6 Text-to-Video**
  - Generates video directly from a text prompt.
  - Supports aspect ratio, duration, and sound options as exposed by the API.

- **Kling 2.6 Motion-Control Image-to-Video**
  - Image-to-video generation with additional motion control parameters.
  - Designed for more directed camera and motion behavior.

- **Seedance V1 Pro (Fast) Image-to-Video**  
  Fast image-to-video generation optimized for quick iteration.

- **Seedance 1.5 Pro Image-to-Video, Text-to-Video**  
  Higher-quality image-to-video generation using the Seedance 1.5 Pro model.


### Utility / Helper Nodes

- **Get Remaining Credits**
  - Return number of credits remaining
  - Useful for verifying that your API key is working
  
- **GridSlice**
  - Splits a grid image (such as 2×2 or 3×3) into individual images for downstream processing.

- **Prompt Grid JSON Parser**
  - Parses structured JSON output (for example, from an LLM) into individual prompt outputs.
  - Designed for multi-image and storyboard-style workflows.

Each node has its own documentation page under `web/docs/` with detailed inputs, outputs, and usage examples.

## Included Example Workflows

This repository includes two example workflows intended as both a test bed and a reference for how these nodes can be used together.

---

### 1) Node Pack Test & Reference Workflow
- Kie-AI-Nodes.json
This workflow includes **all nodes in this pack**, each accompanied by inline notes explaining what the node does and how to use it.

**Recommended first step:**  
Always start by running the **Credits / Account Check** node. This confirms:
- Your Kie.ai API key is installed correctly
- Your account has available credits
- The API is reachable

Once credits are confirmed, you can unmute individual node groups and test them incrementally. This workflow is designed to be a safe environment for validation, learning, and debugging before building custom graphs.

---

### 2) Nano Banana Pro Grid Workflow (Advanced Example)
- Kie-AI-Banana-Pro-Grid.json

This workflow demonstrates a more advanced use case built around **Nano Banana Pro** and grid-based image generation.

**Overview:**
- An optional *face reference image* and a required *source image* are provided
- A language model analyzes the inputs and generates structured prompts
- These prompts are used to generate a **2×2 or 3×3 grid of images**
- The resulting grid is then sliced into individual images using the Grid Slice node

**About the LLM step:**
- This workflow uses an OpenAI Chat LLM node provided by ComfyUI (not part of this node pack)
- This step incurs its own API cost
- You are free to replace this LLM with any compatible model or remove it entirely

**Why this workflow exists:**
This pattern is useful for:
- Generating multiple prompt variations from a single concept
- Creating image sets for downstream video generation
- Breaking large composite images into reusable individual assets

---

Both workflows are meant as **examples**, not strict requirements.  
Feel free to adapt, simplify, or remix them to fit your own pipelines.


## About Kie.ai
Kie.ai is a unified API and model marketplace for image, video, and audio generation. This project is community-maintained and not affiliated with Kie.ai. Learn more at [https://kie.ai](https://kie.ai).

## Credits and usage
Kie.ai uses a credit-based model for requests. There is no subscription requirement, and pay-as-you-go usage is supported.

## Debugging and job visibility
You can review request history and results at [https://kie.ai/logs](https://kie.ai/logs). Some models can take longer to finish; the default timeout has been increased to reduce false failures.

## Sponsorship / Development

This project is developed and maintained with support from **Dreaming Computers**  
[https://dreamingcomputers.com](https://dreamingcomputers.com)

Dreaming Computers is an independent studio exploring AI, creative tooling, and automation-driven workflows. The nodes in this pack are built from practical use cases and ongoing experimentation, and are shared with the community as they evolve.

## Disclaimer
This software is provided as-is. You are responsible for managing your own API usage and credits.

## License
MIT License

Copyright (c) 2025 ComfyUI-Kie-API contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
