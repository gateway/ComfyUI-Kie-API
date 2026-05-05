# KIE GPT Image 2 (Image-to-Image)

Generate an edited or transformed image from a prompt and source images using KIE's GPT Image 2 image-to-image endpoint.

Provider model: `gpt-image-2-image-to-image`

Source docs: https://docs.kie.ai/market/gpt/gpt-image-2-image-to-image

---

## Inputs

- **Prompt**  
  Required text prompt. Maximum length: 20,000 characters.

- **Images**  
  Required ComfyUI image batch. The node uploads up to 16 images and sends those URLs through KIE's `input_urls` field.

- **Aspect Ratio**  
  `auto`, `1:1`, `9:16`, `16:9`, `4:3`, or `3:4`.

- **Resolution**  
  `1K`, `2K`, or `4K`.

- **Log**  
  Enable progress output in the console.

---

## Outputs

- **IMAGE**  
  ComfyUI image tensor (BHWC, float32, range 0-1).

---

## Validation Notes

- Maximum source image inputs: **16**.
- `auto` aspect ratio is only valid with `1K` resolution.
- `1:1` aspect ratio is not valid with `4K` resolution.
- The node uses `input_urls`, matching the live KIE GPT Image 2 I2I API schema.
- The node omits callback/webhook UI and uses the shared async polling flow.

---

## Payload Shape

```json
{
  "model": "gpt-image-2-image-to-image",
  "input": {
    "prompt": "Transform this product image into a premium e-commerce poster style.",
    "input_urls": [
      "https://example.com/source.png"
    ],
    "aspect_ratio": "auto",
    "resolution": "1K"
  }
}
```
