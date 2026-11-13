# KIE GPT Image — native controls

Add **KIE GPT Image (Text-to-Image)** or **KIE GPT Image (Image-to-Image)** for ComfyUI's native V3 DynamicCombo controls. These nodes require a ComfyUI backend and frontend supporting DynamicCombo. No custom JavaScript controls their visibility.

Select the model, then **output mode**:

| Mode | Visible settings |
|---|---|
| Image | Aspect ratio and its supported resolutions; image format; background; compression only for JPEG/WebP |
| SVG | Aspect ratio, resolution, background, SVG author model |
| GIF | Background, frame count and frame duration; per-frame size for Flare/Sunburst text-to-image |

Quality, complexity and moderation appear for 2.6 Flare/Sunburst because they apply to all three output modes. Economy omits those controls and resolution; Economy GIF retains its supported aspect-ratio selector. Economy image-to-image and older models expose only Image mode. JPEG exposes only opaque background. Static resolution controls are absent from standard GIF branches.

For 2.6 Flare/Sunburst image-to-image, **edit guide** selects:

- **None:** reference images only; no guide sockets.
- **Mask:** one MASK socket, only in Image mode. 1 means edit; dimensions must match the first source image.
- **Markup:** annotation IMAGE and transparency MASK sockets. Connect the two outputs of Load Image for a separate transparent annotation PNG. 1 in markup_mask means transparent. Explain the marked change in the prompt.

Mask and Markup are mutually exclusive native branches. The existing backend still validates values and media before uploading or submitting, including requests made through the API. Unsupported options cannot become valid merely by bypassing the browser. Inactive branch values are not forwarded.

Outputs retain the order **image, mask, file_paths, svg, metadata**. Original files are saved under ComfyUI's output/kie_gpt_image directory. GIF returns all frames with timing in metadata; SVG returns file paths and text with no IMAGE/MASK. See the existing [text-to-image](KIE_GPTImage2_TextToImage.md) and [image-to-image](KIE_GPTImage2_ImageToImage.md) references for provider limits, alpha conventions and output details.

## Existing workflows

Saved workflows and API prompts using `KIE_GPTImage2_TextToImage` or `KIE_GPTImage2_ImageToImage` retain their original flat inputs, widget order, socket order and execution behavior. They display **[Legacy]** on installations supporting the native nodes. They are not automatically rewritten or replaced.

The native IDs are `KIE_GPTImage_TextToImage` and `KIE_GPTImage_ImageToImage`. To adopt native controls in an existing workflow, add the corresponding new node, select its settings, and reconnect its inputs/outputs. Keep the legacy node until the replacement is tested. Loading an old workflow alone does not migrate it.

On older backends without the native API, legacy nodes remain registered and the rest of this node pack continues to load. Update both ComfyUI and its frontend to use the native nodes. Restart ComfyUI and refresh the browser after pulling the update.

## Verification

Mac checks cover Python compilation, dependency-free schema structure/request translation tests, legacy schema compatibility, and legacy JavaScript isolation. These checks do not render ComfyUI or execute its runtime. No Torch or ComfyUI runtime dependencies were installed on the Mac.

On Windows, from this repository with the ComfyUI Python interpreter:

```text
python -m unittest discover -s tests -p "test_gpt_image*.py"
```

The native runtime tests use the installed ComfyUI schema and nested-input parser, with provider calls mocked. The standard ComfyUI/custom_nodes layout is detected; for another layout, add the ComfyUI source directory to PYTHONPATH. A recent DynamicCombo-capable ComfyUI installation is required.

Browser verification remains necessary: add each native node; select all models and available output modes; verify guide sockets, quality/complexity, compression and resolution visibility; save/reload and clone a native node; then load an older workflow and confirm its values and connections are unchanged. First run the mocked tests, then make small provider requests as needed. Kie's existing SVG-editing/transparency documentation discrepancies remain live-test items.

Architecture checked against [ComfyUI's DynamicCombo documentation](https://docs.comfy.org/custom-nodes/v3_migration#dynamiccombo) and the official loader/server code on 2026-11-13. The pack's mixed registry keeps existing V1 nodes while ComfyUI recognizes the new V3 classes and exposes their native schemas.
