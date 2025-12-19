# KIE Seedance V1 Pro Fast (I2V)

Convert a single reference image plus prompt into a short video clip using
ByteDance’s rapid Seedance V1 Pro image-to-video model.

---

## Inputs

- **Prompt**  
  Describe how the source image should animate.

- **Images**  
  ComfyUI image tensor batch. Only the first frame is uploaded.

- **Resolution**  
  Choose 720p for faster jobs or 1080p for higher quality.

- **Duration**  
  Output length (5s or 10s).

- **Poll Interval**  
  How often to check the task status (seconds).

- **Timeout**  
  Maximum time to wait before failing (seconds).

- **Log**  
  Enable console logging for troubleshooting.

---

## Outputs

- **VIDEO**  
  Path to a temporary `.mp4` file saved to disk. Downstream nodes can consume this file immediately.

---

## Notes

- The reference image is uploaded temporarily to the KIE API.
- Credits are consumed per request. Monitor remaining credits with the provided node.
- Video rendering can take a minute or more depending on resolution and duration.

## Debugging
Visit https://kie.ai/logs to monitor job progress or retrieve outputs if the node times out.
