# KIE Kling 2.6 (Text-to-Video)

Generate a short video clip from a text prompt using the Kling 2.6 text-to-video model.

---

## Inputs

- **prompt**
  Text prompt describing the desired video.

- **sound**
  Include audio in the output video (true/false).

- **aspect_ratio**
  Choose from 1:1, 16:9, or 9:16.

- **duration**
  Output length in seconds: 5 or 10.

- **log**
  Enable console logging.

---

## Output

- **VIDEO**
  ComfyUI VIDEO output compatible with the SaveVideo node.

---

## Example

Prompt:
"A calm sunrise over a misty lake, with slow drifting fog and soft golden light."

---

## Notes

- Aspect ratio and duration must match the allowed enums.
- Sound increases generation cost and may affect runtime.
- This node uses internal defaults for polling/retries/timeouts (not exposed in the UI).
