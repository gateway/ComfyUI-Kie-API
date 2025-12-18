i# KIE Model Implementation Template

This document defines the REQUIRED structure and conventions for adding new
KIE API models to this repository.

All new models MUST follow this template to ensure:
- ComfyUI compatibility
- shared polling & error handling
- consistent logging
- minimal duplication

---

## File Placement

Each KIE model MUST live in its own file:

kie_api/<model_name>.py

i
Examples:
- nanobanana.py
- seedream45.py
- veo3.py

---

## Required Imports

Models MUST reuse shared helpers. Do NOT duplicate logic.

```python
from typing import Any

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import create_task, poll_task_until_complete
from .images import image_bytes_to_comfy_tensor
from .http import TransientKieError
from .log import log

Required Constants

Each model MUST define:

MODEL_NAME = "<exact model name from KIE docs>"

Optional:

ASPECT_RATIO_OPTIONS = [...]
RESOLUTION_OPTIONS = [...]
OUTPUT_FORMAT_OPTIONS = [...]

Required Public Entry Function

Each model MUST expose exactly ONE public runner:

def run_<model_name>(
    *,
    prompt: str,
    image_inputs: list[bytes] | None,
    aspect_ratio: str,
    resolution: str,
    output_format: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
) -> torch.Tensor:

Rules:

-MUST validate required inputs
-MUST create task via create_task(...)
-MUST poll via poll_task_until_complete(...)
-MUST return ComfyUI IMAGE tensor (BHWC, float32, 0–1)
-MUST NOT print directly (use log helper)

Logging Rules

-Logging is controlled by log: bool
-Use shared logger only
-Avoid dumping full JSON payloads
-Summarize state transitions only

Good:

[KIE] Task <id> state: waiting (elapsed=30s)


Bad:

[KIE] Full recordInfo JSON: {...huge...}

Error Handling Rules
Use RuntimeError when:

-user input is invalid
-model fails permanently
-decoding output fails
Use TransientKieError when:
-API reports temporary failure
-retry is reasonable

Never swallow exceptions silently.

Image Output Requirements (ComfyUI)

All image outputs MUST:

-be torch.Tensor
-shape: [B, H, W, C]
-dtype: float32
-range: 0.0 – 1.0
-reside on CPU

Use ONLY:

image_bytes_to_comfy_tensor(...)


Forbidden Patterns ❌

-No polling loops inside nodes.py
-No direct requests calls in nodes.py
-No torch.frombuffer on raw bytes
-No duplicated polling code
-No printing directly to console

Node Layer Responsibility

Nodes MUST:

-define INPUT_TYPES
-define RETURN_TYPES
-call exactly one model runner
-never perform HTTP or polling logic

Versioning

Each model file SHOULD include a header comment:

# Model: Seedream 4.5
# API version: 2025-xx
# KIE Docs: <url>

