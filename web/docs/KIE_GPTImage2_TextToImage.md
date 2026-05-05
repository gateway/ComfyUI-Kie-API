# KIE GPT Image 2 (Text-to-Image)

Generate an image from a text prompt using KIE's GPT Image 2 text-to-image endpoint.

Provider model: `gpt-image-2-text-to-image`

Source docs: https://docs.kie.ai/market/gpt/gpt-image-2-text-to-image

---

## Inputs

- **Prompt**  
  Required text prompt. Maximum length: 20,000 characters.

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

- `auto` aspect ratio is only valid with `1K` resolution.
- `1:1` aspect ratio is not valid with `4K` resolution.
- The node omits callback/webhook UI and uses the shared async polling flow.

---

## Payload Shape

```json
{
  "model": "gpt-image-2-text-to-image",
  "input": {
    "prompt": "A cinematic night city poster with neon reflections on a rainy street.",
    "aspect_ratio": "auto",
    "resolution": "1K"
  }
}
```
