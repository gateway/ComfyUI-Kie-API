# KIE GPT Image (Text-to-Image)

Generate or edit images with GPT Image 2, GPT Image 2.5 Flare, or GPT Image 2.5 Sunburst.

## Inputs

- **Prompt:** Required multiline text, up to 20,000 characters.
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
- Reuses the shared task, upload, polling, download and transient retry helpers. No callback widget is exposed.

## Outputs

- **IMAGE / image:** RGB `[B,H,W,3]`, float32, range 0–1. Remains at output slot 0.
- **MASK / mask:** Inverse alpha `[B,H,W]`, float32, range 0–1. 1 is transparent, 0 is opaque. Opaque results yield zeros at image resolution.

For transparent PNG output, connect IMAGE and MASK to ComfyUI's **Join Image with Alpha**, then save its output. Saving RGB alone discards transparency. MASK describes output transparency, not an input editing mask.

## Compatibility

Internal ID `KIE_GPTImage2_TextToImage` is unchanged. Model and background widgets are appended after existing widgets; missing values default to GPT Image 2 and opaque. Existing image connections retain slot 0. The visible name is now **KIE GPT Image (Text-to-Image)**.

Restart ComfyUI and refresh the browser after updating.

## Provider models and sources

Verified against Kie documentation on 2026-10-06:

- [GPT Image 2](https://docs.kie.ai/market/gpt/gpt-image-2-text-to-image): `gpt-image-2-text-to-image`
- [Flare](https://docs.kie.ai/market/gpt/gpt-image-2-5-flare-text-to-image): `gpt-image-2-5-flare-text-to-image`
- [Sunburst](https://docs.kie.ai/market/gpt/gpt-image-2-5-sunburst-text-to-image): `gpt-image-2-5-sunburst-text-to-image`

Pinned ratios follow the actual schema `enum` and Kie model page, not extra labels in I2I documentation's `x-apidog-enum` metadata.

## Verification

Mac checks cover syntax and static review only. No paid generation or ComfyUI runtime verification has been performed here.

On Windows, from this repository using the ComfyUI Python environment:

```text
python -m unittest discover -s tests -p "test_gpt_image*.py"
```

Load an older GPT Image 2 workflow and verify its prompt, ratio, resolution, logging and image connection. Generate with each 2.5 model in both modes; exercise auto at 2K/4K, 1K-only ratios, invalid connected inputs, and transparency via Join Image with Alpha. Save/reload and verify selections. These UI/live checks remain pending.
