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

## Image Nodes
- **Nano Banana Pro Image**
  - Image generation node using the Googles Nano Banana Pro model
  - Supports up to 8 optional input/reference images.
- **Nano Banana 2**
  - Image generation node using Nano Banana 2.
  - Supports up to 14 optional input/reference images.
  - Supports optional Google web-search grounding.
- **Seedream Text-to-Image / Edit**
  - Text-to-image and image-editing node for Seedream models.
  - Supports prompt-based generation and edits (edit node accepts up to 14 input images).
- **Flux 2 Image-to-Image (Pro/Flex)**
  - Image-to-image node with a model dropdown for Pro or Flex.
  - Accepts 1–8 input images via ComfyUI batch.
- **Grok Imagine Text-to-Image**
  - Generates one or more images from a text prompt.
  - Returns the image batch plus a `task_id` for downstream Grok I2V chaining.
- **Grok Imagine Image-to-Image**
  - Generates one or more edited images from a single uploaded source image.
  - Returns the image batch plus a `task_id` for downstream Grok I2V chaining.

## Video Nodes
- **Kling 2.6 Image-to-Video**
  - Generates video from a single input image.
  - Uses the Kling 2.6 image-to-video model.
- **Kling 2.5 I2V Pro**
  - Generates video from a required first image and optional tail image.
  - Uses the Kling 2.5 Turbo image-to-video Pro model.
- **Kling 2.6 Text-to-Video**
  - Generates video directly from a text prompt.
  - Supports aspect ratio, duration, and sound options as exposed by the API.
- **Grok Imagine Text-to-Video**
  - Generates video directly from a text prompt.
  - Supports aspect ratio, mode, duration, and resolution options from the KIE Grok Imagine API.
- **Grok Imagine Image-to-Video**
  - Generates video from either one uploaded external image or a Grok image-generation task reference.
  - Supports `task_id` + `index` selection for animating one of Grok's generated images.
- **Kling 2.6 Motion-Control Image-to-Video**
  - Image-to-video generation with additional motion control parameters.
  - Designed for more directed camera and motion behavior.
- **Kling 3.0 Motion-Control Image-to-Video**
  - Generates video from a required reference image and a required motion-driver video.
  - Mirrors the Kling 2.6 motion-control node shape with Kling 3.0 model routing.
  - Keeps prompt optional and returns a ComfyUI VIDEO output.
- **Kling 3.0 (Video)**
  - Supports single-shot or multi-shot generation.
  - Supports optional first/last frame control and named element references.
  - In multi-shot mode, total duration is computed from shot durations (max 15s).
  - Optional `kling_data` input allows direct execution from preflight-validated payloads.
  - **Experimental / development status:** not production-ready yet.
- **Seedance V1 Pro (Fast) Image-to-Video**  
  Fast image-to-video generation optimized for quick iteration.
- **Seedance 1.5 Pro Image-to-Video, Text-to-Video**  
  Higher-quality image-to-video generation using the Seedance 1.5 Pro model.

## LLM Nodes
- **Gemini (LLM) [Experimental]**
  - Text generation node using Gemini 2.5/3 Pro/Flash chat completions.
  - Supports role selection, media inputs (images/video/audio), optional reasoning output, and Google Search toggle.

## Audio Nodes
- **Suno Music (Basic)**
  - Minimal inputs: title, style, prompt, model, instrument, tags, gender.
  - Returns two AUDIO outputs + two cover images via KIE Suno API `generate` + `record-info` polling.
- **Suno Music (Advanced)**
  - Adds style/creative weights to the Basic node.
  - Returns two AUDIO outputs + two cover images via KIE Suno API `generate` + `record-info` polling.

## Utility / Helper Nodes

- **Get Remaining Credits**
  - Return number of credits remaining
  - Useful for verifying that your API key is working
  
- **GridSlice**
  - Splits a grid image (such as 2×2 or 3×3) into individual images for downstream processing.

- **Prompt Grid JSON Parser**
  - Parses structured JSON output (for example, from an LLM) into individual prompt outputs.
  - Designed for multi-image and storyboard-style workflows.
- **System Prompt Selector**
  - Combines a user prompt with a system prompt template from `prompts/`.
  - See [prompts/README.md](prompts/README.md) for creating new templates.
- **Kling Elements + Kling Elements Batch**
  - Build named Kling elements (image/video) and batch them for Kling 3.0 prompts using `@element_name`.
- **Kling 3.0 Preflight**
  - Validates/uploads inputs and returns exact createTask payload JSON without running generation.
  - Outputs `kling_data` for direct chaining into `Kling 3.0 (Video)`.
  - Recommended before using Kling 3.0 generation while the node is in development.

## Documentation Hub

Use this section after reviewing Current Available Nodes.

- Full docs index (all nodes): [`web/docs/README.md`](web/docs/README.md)
- Kling 3.0 motion status: implemented in this repo with both the node doc and API spec linked below.
- Grok Imagine status: `T2I`, `I2I`, `T2V`, and `I2V` are implemented in this repo.
- Grok Imagine node docs:
  - [`web/docs/KIE_GrokImagine_T2I.md`](web/docs/KIE_GrokImagine_T2I.md) - Grok Imagine text-to-image node reference.
  - [`web/docs/KIE_GrokImagine_I2I.md`](web/docs/KIE_GrokImagine_I2I.md) - Grok Imagine image-to-image node reference.
  - [`web/docs/KIE_GrokImagine_T2V.md`](web/docs/KIE_GrokImagine_T2V.md) - Grok Imagine text-to-video node reference.
  - [`web/docs/KIE_GrokImagine_I2V.md`](web/docs/KIE_GrokImagine_I2V.md) - Grok Imagine image-to-video node reference.
- Kling 3.0 motion docs:
  - [`web/docs/KIE_Kling3_Motion_I2V.md`](web/docs/KIE_Kling3_Motion_I2V.md) - Kling 3.0 motion-control node reference.
  - [`web/docs/KIE_Kling3_Motion_I2V_Spec.md`](web/docs/KIE_Kling3_Motion_I2V_Spec.md) - Kling 3.0 motion-control image-to-video API reference.
- API specs:
  - [`web/docs/KIE_GrokImagine_T2V_Spec.md`](web/docs/KIE_GrokImagine_T2V_Spec.md) - Grok Imagine text-to-video API reference.
  - [`web/docs/KIE_GrokImagine_I2V_Spec.md`](web/docs/KIE_GrokImagine_I2V_Spec.md) - Grok Imagine image-to-video API reference.
  - [`web/docs/KIE_GrokImagine_T2I_Spec.md`](web/docs/KIE_GrokImagine_T2I_Spec.md) - Grok Imagine text-to-image API reference.
  - [`web/docs/KIE_GrokImagine_I2I_Spec.md`](web/docs/KIE_GrokImagine_I2I_Spec.md) - Grok Imagine image-to-image API reference.
- Recommended Kling 3 reading order:
  - [`web/docs/KIE_Kling_Elements.md`](web/docs/KIE_Kling_Elements.md)
  - [`web/docs/KIE_Kling_Elements_Batch.md`](web/docs/KIE_Kling_Elements_Batch.md)
  - [`web/docs/KIE_Kling3_Preflight.md`](web/docs/KIE_Kling3_Preflight.md)
  - [`web/docs/KIE_Kling3_Video.md`](web/docs/KIE_Kling3_Video.md)
  - [`web/docs/KIE_Kling3_Motion_I2V.md`](web/docs/KIE_Kling3_Motion_I2V.md)
  - [`web/docs/KIE_Kling3_Motion_I2V_Spec.md`](web/docs/KIE_Kling3_Motion_I2V_Spec.md)
- Example workflows:
  - [`Kie-AI-Nodes.json`](Kie-AI-Nodes.json)
  - [`Kie-AI-Banana-Pro-Grid.json`](Kie-AI-Banana-Pro-Grid.json)
  - [`KIE-AI-Banana-Pro-Banana-Pro.json`](KIE-AI-Banana-Pro-Banana-Pro.json)
  - [`example_workflows/Kie AI - Kling 3.0 Motion.json`](example_workflows/Kie%20AI%20-%20Kling%203.0%20Motion.json)

## Included Example Workflows

This repository includes several example workflows intended as both a test bed and a reference for how these nodes can be used together.

---

### 1) Node Pack Test & Reference Workflow
**Kie-AI-Nodes.json**

This workflow includes **all nodes in this pack**, each accompanied by inline notes explaining what the node does and how to use it.

**Recommended first step:**  
Always start by running the **Credits / Account Check** node. This confirms:
- Your Kie.ai API key is installed correctly
- Your account has available credits
- The API is reachable

Once credits are confirmed, you can unmute individual node groups and test them incrementally. This workflow is designed to be a safe environment for validation, learning, and debugging before building custom graphs.

---

### 2) Nano Banana Pro Grid Workflow (Advanced Example)
**Kie-AI-Banana-Pro-Grid.json**

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

These workflows are meant as **examples**, not strict requirements.  
Feel free to adapt, simplify, or remix them to fit your own pipelines.

---

### 3) Nano Banana Pro + Nano Banana 2 Comparison Workflow
**KIE-AI-Banana-Pro-Banana-Pro.json**

This workflow is focused on direct comparison between **Nano Banana Pro** and **Nano Banana 2** in a single graph.

**Overview:**
- Uses matching prompt structure to compare output behavior side by side
- Includes Nano Banana 2 runs with optional web-search grounding
- Supports reference-image driven comparisons for iterative testing

This is useful for quickly evaluating model preference by prompt type, fidelity, and cost/performance tradeoffs.

---

### 4) Kling 3.0 Motion-Control Workflow
**Kie AI - Kling 3.0 Motion.json**

This workflow is focused on **Kling 3.0 Motion-Control** using:
- one reference image
- one motion-driver video
- an optional prompt for extra control

**Overview:**
- Transfers motion from a driver video onto the subject from a still image
- Exposes Kling 3.0 motion settings such as `character_orientation` and resolution mode
- Useful for directed image-to-video tests where identity comes from the image and movement comes from the video

Related docs:
- [`web/docs/KIE_Kling3_Motion_I2V.md`](web/docs/KIE_Kling3_Motion_I2V.md)
- [`web/docs/KIE_Kling3_Motion_I2V_Spec.md`](web/docs/KIE_Kling3_Motion_I2V_Spec.md)

## Changelog
- 2026-03-12: Bumped package version to 0.1.12 and fixed stale media upload caching risk by forcing unique upload filenames per run.
- 2026-03-12: Added README coverage for the Kling 3.0 Motion-Control workflow and bumped package version to 0.1.11.
- 2026-03-12: Added the Kling 3.0 Motion-Control node and synced docs/spec coverage.
- 2026-03-12: Added the Kling 3.0 Motion-Control API spec doc.
- 2026-03-07: Synced README/docs coverage for Grok Imagine T2I, I2I, T2V, and I2V, and bumped version to 0.1.10.
- 2026-03-07: Added the Grok Imagine text-to-video node and synced docs/spec references.
- 2026-03-07: Added the Grok Imagine image-to-video node and synced docs/spec references.
- 2026-03-07: Added the Grok Imagine text-to-image node and synced docs/spec references.
- 2026-03-07: Added the Grok Imagine image-to-image node and synced docs/spec references.
- 2026-03-07: Added Grok Imagine text-to-image and image-to-image API spec docs.
- 2026-02-28: Added new example workflow `KIE-AI-Banana-Pro-Banana-Pro.json` to repository docs.
- 2026-02-28: Documentation clarified Nano Banana Pro (up to 8 images) and Nano Banana 2 (up to 14 images + optional Google web search). Bumped version to 0.1.8.
- 2026-02-28: Updated Nano Banana Pro + Nano Banana 2 payload behavior to always send `image_input` (empty list when no images are connected).
- 2026-02-28: Added Nano Banana 2 image node with Google search toggle.
- 2026-01-30: Added Flux 2 Image-to-Image node (Pro/Flex) with model dropdown.
- 2026-01-30: Added Gemini 3 Pro LLM node (phase 1, experimental).
- 2026-01-30: Gemini 3 Pro LLM updated with role dropdown and media inputs (phase 1.5).
- 2026-01-30: Gemini 3 Pro LLM updated with audio input support.
- 2026-02-01: Added Suno Music nodes (Basic and Advanced), returning two songs and two cover images.
- 2026-02-11: Added Kling 3.0 video node and helper nodes for Kling elements + element batching.
- 2026-02-11: Added Kling 3.0 preflight node to validate and preview request payloads before generation.
- 2026-02-11: Standardized Kling 3 preflight/task chaining on `kling_data`.
- 2026-02-11: Updated Kling 3 payload compatibility (aspect ratio + multi-shot sound handling).
- 2026-02-11: Cleaned up README structure and added docs index coverage for all public nodes.
- 2026-02-11: Increased default async video polling timeout from 1000s to 2000s.

## About Kie.ai
Kie.ai is a unified API and model marketplace for image, video, and audio generation. This project is community-maintained and not affiliated with Kie.ai. Learn more at [https://kie.ai](https://kie.ai?ref=e7565cf24a7fad4586341a87eaf21e42).

## Credits and usage
Kie.ai uses a credit-based model for requests. There is no subscription requirement, and pay-as-you-go usage is supported.

## Debugging and job visibility
You can review request history and results at [https://kie.ai/logs](https://kie.ai/logs). Some models can take longer to finish; the default async timeout is set to 2000s to reduce false failures.

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
