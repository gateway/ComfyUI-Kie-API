# KIE GPT Image (Image-to-Image)

Use GPT Image 2, 2.5 Flare/Sunburst, or 2.6 Flare/Sunburst/Economy in the existing node. The baseline inputs below describe 2/2.5; the 2.6 additions are documented afterward.

## Inputs

- **Prompt:** Required multiline text, up to 20,000 characters.
- **Images:** Required RGB image batch, up to 16 reference images. Uploaded URLs are sent as `input_urls`.
- **Model:** `GPT Image 2` (default), `GPT Image 2.5 Flare`, or `GPT Image 2.5 Sunburst`.
- **Aspect ratio:** Model-dependent choices, default `auto`.
- **Resolution:** `1K` (default), `2K`, or `4K`, restricted by aspect ratio.
- **Background:** `opaque` (default), `transparent`, or `auto` for 2.5. GPT Image 2 offers only `opaque`; its API payload omits background.
- **Log:** Console progress output.

GPT Image 2 supports `auto`, `1:1`, `9:16`, `16:9`, `4:3`, and `3:4`.
GPT Image 2.5 also supports `3:2`, `2:3`, `21:9`, `27:16`, `16:27`, `9:8`, and `8:9`.

## Validation

- GPT Image 2: `auto` requires 1K; `1:1` permits 1K and 2K only.
- GPT Image 2.5: `27:16`, `16:27`, `9:8`, and `8:9` require 1K; other listed ratios permit all three resolutions.
- Changing model or aspect ratio refreshes dropdowns and resets incompatible widget selections to the first allowed value. Loading saved workflows does not normalize saved values.
- Python validates before uploads or submission, including connected inputs and headless API workflows.
- GPT Image 2.5 rejects batches over 16 before upload. GPT Image 2 retains its existing warning and first-16 truncation behavior.
- Reuses the shared task, upload, polling, download and transient retry helpers. No callback widget is exposed.

## Outputs

- **IMAGE / image:** RGB `[B,H,W,3]`, float32, range 0–1. Remains at output slot 0.
- **MASK / mask:** Inverse alpha `[B,H,W]`, float32, range 0–1. 1 is transparent, 0 is opaque. Opaque results yield zeros at image resolution.

For transparent PNG output, connect IMAGE and MASK to ComfyUI's **Join Image with Alpha**, then save its output. Saving RGB alone discards transparency. MASK describes output transparency, not an input editing mask.

## Compatibility

Internal ID `KIE_GPTImage2_ImageToImage` is unchanged. Model and background widgets are appended after existing widgets; missing values default to GPT Image 2 and opaque. Existing image connections retain slot 0. The visible name is now **KIE GPT Image (Image-to-Image)**.

Restart ComfyUI and refresh the browser after updating.

## Provider models and sources

Verified against Kie documentation on 2026-10-06:

- [GPT Image 2](https://docs.kie.ai/market/gpt/gpt-image-2-image-to-image): `gpt-image-2-image-to-image`
- [Flare](https://docs.kie.ai/market/gpt/gpt-image-2-5-flare-image-to-image): `gpt-image-2-5-flare-image-to-image`
- [Sunburst](https://docs.kie.ai/market/gpt/gpt-image-2-5-sunburst-image-to-image): `gpt-image-2-5-sunburst-image-to-image`

Pinned ratios follow the actual schema `enum` and Kie model page, not extra labels in I2I documentation's `x-apidog-enum` metadata.

## Verification

Baseline Mac checks cover syntax and static review; see the 2.6 verification section for additional lightweight tests. No paid generation or ComfyUI runtime verification has been performed here.

On Windows, from this repository using the ComfyUI Python environment:

```text
python -m unittest discover -s tests -p "test_gpt_image*.py"
```

Load an older GPT Image 2 workflow and verify its prompt, ratio, resolution, logging and image connection. Generate with each 2.5 model in both modes; exercise auto at 2K/4K, 1K-only ratios, invalid connected inputs, and transparency via Join Image with Alpha. Save/reload and verify selections. These UI/live checks remain pending.

## GPT Image 2.6

The existing model dropdown also includes **GPT Image 2.6 Flare**, **Sunburst**, and **Economy**. Flare/Sunburst support prompts up to 32,000 characters; Economy remains at 20,000 and 1K. Model and mode determine the permitted output formats. New controls are appended after existing widgets; inactive advanced controls are hidden and omitted from requests.

| Control | Meaning |
|---|---|
| output_format | Flare/Sunburst: PNG, JPEG, WebP, GIF, SVG. Economy choices depend on mode. |
| quality | Rendering detail: medium (default), low, high, xhigh, max, auto. Flare/Sunburst only. |
| complexity | Planning effort: high (default), medium, low. Independent of quality. |
| moderation | Kie filtering level: low (provider default) or auto. |
| output_compression | JPEG/WebP only, 0–100. |
| frame_count | GIF only: Flare/Sunburst 2–16; Economy auto, 4, 9, 16, 25, 36, 64. |
| frame_duration_ms | GIF only: 20–2000, multiples of 10. Default 200. |
| gif_size | Flare/Sunburst T2I GIF only: auto or frame dimensions such as 512x512. |
| svg_model | SVG author model: gpt-5.6-luna (default), gpt-6-sol, gpt-5.6-terra. |

2.6 Flare/Sunburst aspect ratios: auto, 1:1, 3:2, 2:3, 4:3, 3:4, 5:4, 4:5, 16:9, 9:16, 2:1, 1:2, 21:9, 9:21, 3:1, 1:3. Economy: auto, 1:1, 16:9, 9:16, 3:2, 2:3, 21:9, 4:3. Older model ratios/restrictions remain unchanged.

Resolution tiers are provider labels: square 4K is 2880×2880, not 4096×4096. Standard GIF requests omit static aspect ratio/resolution. T2I uses gif_size and validates the provider sprite-sheet budget; 512x512 works for all supported frame counts. The I2I contract does not expose size, so gif_size is ignored there. Economy omits resolution from the payload and uses its own GIF frame-count encoding.

Flare/Sunburst use token billing, including extra author-model usage for SVG. No pricing estimate is treated as a spending cap. Kie lists SVG editing even though OpenAI's direct editing guide does not; this implementation follows Kie's contract. Kie's transparency documentation is inconsistent about resolution and GIF/SVG. These combinations need live verification; JPEG with transparent background is rejected locally.

### New outputs and saved files

The first two sockets remain IMAGE and MASK. The three appended STRING sockets are:

- **file_paths:** JSON array of absolute paths to every original provider file, automatically saved under ComfyUI's `output/kie_gpt_image/` directory using unique names.
- **svg:** Native SVG XML text, empty for raster outputs. If a provider returns multiple SVG documents, this is a JSON array of their texts; individual files remain available through file_paths.
- **metadata:** JSON containing task_id and an outputs array with paths, URLs, format, MIME type and byte size. Raster records include dimensions/frame count; GIF records include per-frame durations and loop metadata.

GIF IMAGE/MASK outputs contain every decoded frame in order. Saving the IMAGE batch alone loses animation timing; use the original GIF file, or use metadata timings when rebuilding animation. SVG outputs have **no IMAGE or MASK** (`None`); connect only the STRING outputs for SVG workflows. No rasterization dependency is installed and no placeholder image is generated. SVG text is returned as data, not rendered or executed.

All original files are retained. Multiple raster outputs must have matching dimensions to form a ComfyUI IMAGE batch; if they differ, the error identifies the saved originals. Output content is checked against the selected 2.6 format, so an unexpected raster response is not silently accepted as SVG/GIF.

### 2.6 verification

Mac verification covers Python syntax, dependency-free payload tests, node schema checks, and headless widget lifecycle tests. Torch/Pillow runtime tests are supplied for the Windows ComfyUI environment; they are not executed on the Mac. No paid 2.6 generation has been performed.

Run in this repository on Windows using ComfyUI's Python interpreter:

```text
python -m unittest discover -s tests -p "test_gpt_image*.py"
```

Then verify six routes with small PNG requests, both edit-guide paths, a short GIF (inspect animation and timings), and an SVG (inspect its file/text). Verify saved 2/2.5 workflows and switching models/formats, including connected selectors. Kie SVG editing and transparency beyond 1K remain provider smoke-test cases. Reload ComfyUI and refresh the browser before testing.

Sources checked 2026-11-11: [Kie market and live API tabs](https://kie.ai/gpt-image-2-6), [Flare T2I](https://docs.kie.ai/market/gpt/gpt-image-2-6-flare-text-to-image), [Flare I2I](https://docs.kie.ai/market/gpt/gpt-image-2-6-flare-image-to-image), [Economy T2I](https://docs.kie.ai/market/gpt/gpt-image-2-6-economy-text-to-image), [Economy I2I](https://docs.kie.ai/market/gpt/gpt-image-2-6-economy-image-to-image).

### Connecting an edit guide

Economy I2I returns PNG only. Mask and markup inputs are available for 2.6 Flare/Sunburst; older models and Economy reject connected guides before any upload.

For **mask editing**, connect a single ComfyUI MASK matching the first source image: 1 means edit, 0 means preserve. The node encodes it as an RGBA PNG with alpha = 1 − mask and sends its uploaded URL as mask_url. Masks cannot be combined with GIF/SVG output.

For **markup editing**, create a separate transparent annotation PNG with a visible rectangle, circle, or arrow. Load that PNG separately: connect its IMAGE to markup and its MASK to markup_mask. Both must match the first source image dimensions. RGB markup requires markup_mask; an RGBA tensor may instead carry its own alpha, in which case leave markup_mask disconnected. Do not flatten annotations onto the photograph. The node uploads the annotation as markup. Explain the change in the prompt, e.g. “Replace the mug inside the red rectangle with a blue mug; preserve the table and lighting.”

Never connect mask and markup together. Validation rejects mismatched dimensions, batches of guides, missing annotation alpha, nonfinite/out-of-range values, and entirely opaque or invisible markup. Mask/markup apply to the first reference; other source images remain references. These are model guidance, not a guarantee that every pixel outside the region is preserved.
