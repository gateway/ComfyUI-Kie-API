# Frontend extensions

`gpt_image.js` refreshes GPT Image aspect-ratio, resolution and background choices from Python's `kie_model_options` metadata. It uses ComfyUI extension hooks and per-widget callbacks, without replacing node prototypes.

The package exports `WEB_DIRECTORY = "./js"`. Restart ComfyUI and refresh the browser after updating. Python remains authoritative for connected inputs and headless API workflows.

Per-instance configure and connection handlers refresh cloned nodes and offer all potentially valid options when a controlling input is linked. Existing handlers and saved values are preserved.

Widget regression cases: `node --test tests/gpt_image_widgets.test.mjs`. These cases are syntax-checked and statically reviewed on the Mac; execution and actual ComfyUI clone, save/reload, and connect/disconnect checks remain pending.
