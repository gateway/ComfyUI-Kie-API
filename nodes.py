import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Tuple

import requests
import torch
from PIL import Image


KIE_KEY_PATH = Path(__file__).resolve().parent / "config" / "kie_key.txt"
API_URL = "https://api.kie.ai/api/v1/chat/credit"
CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
UPLOAD_URL = "https://kieai.redpandaai.co/api/file-stream-upload"
MODEL_NAME = "nano-banana-pro"
ASPECT_RATIO_OPTIONS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "auto"]
RESOLUTION_OPTIONS = ["1K", "2K", "4K"]
OUTPUT_FORMAT_OPTIONS = ["png", "jpg"]
UPLOAD_PATH = "images/user-uploads"


def _load_api_key() -> str:
    try:
        api_key = KIE_KEY_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "KIE API key not found. Please create config/kie_key.txt with your API key."
        ) from exc
    if not api_key:
        raise RuntimeError("KIE API key file is empty. Please add your key to config/kie_key.txt.")
    return api_key


def _fetch_remaining_credits(api_key: str) -> Tuple[str, int]:
    try:
        response = requests.get(
            API_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=30
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call remaining credits endpoint: {exc}") from exc

    raw_text = response.text
    try:
        payload: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Remaining credits endpoint did not return valid JSON.") from exc

    code = payload.get("code")
    msg = payload.get("msg")
    data = payload.get("data")

    if code != 200:
        raise RuntimeError(f"Remaining credits endpoint returned error code {code}: {msg}")

    try:
        credits_remaining = int(data)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Remaining credits value is not an integer.") from exc

    return raw_text, credits_remaining


def _log(enabled: bool, msg: str) -> None:
    if enabled:
        print(f"[KIE] {msg}")


def _log_remaining_credits(log: bool, record_data: dict[str, Any], api_key: str) -> None:
    if not log:
        return

    remaining = record_data.get("remainedCredits")
    if remaining is not None:
        _log(True, f"Remaining credits: {remaining}")
        return

    try:
        _raw, credits_remaining = _fetch_remaining_credits(api_key)
        _log(True, f"Remaining credits: {credits_remaining}")
    except Exception as exc:
        _log(True, f"Failed to fetch remaining credits: {exc}")


def _truncate_url(url: str, max_length: int = 80) -> str:
    if len(url) <= max_length:
        return url
    return url[:max_length] + "..."


class TransientKieError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _validate_prompt(prompt: str) -> None:
    if not prompt:
        raise RuntimeError("Prompt is required.")
    if len(prompt) > 10000:
        raise RuntimeError("Prompt exceeds the maximum length of 10000 characters.")


def _create_nano_banana_task(api_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    try:
        response = requests.post(
            CREATE_TASK_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call createTask endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"createTask returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("createTask endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("message") or payload_json.get("msg")
        raise RuntimeError(f"createTask endpoint returned error code {payload_json.get('code')}: {message}")

    task_id = (payload_json.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError("createTask endpoint did not return a taskId.")

    return task_id, response.text


def _fetch_task_record(api_key: str, task_id: str) -> tuple[dict[str, Any], str, Any]:
    try:
        response = requests.get(
            RECORD_INFO_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"taskId": task_id},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call recordInfo endpoint: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"recordInfo returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    raw_text = response.text
    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("recordInfo endpoint did not return valid JSON.") from exc

    if payload_json.get("code") != 200:
        message = payload_json.get("message") or payload_json.get("msg")
        raise RuntimeError(f"recordInfo endpoint returned error code {payload_json.get('code')}: {message}")

    data = payload_json.get("data")
    if data is None:
        raise RuntimeError("recordInfo endpoint returned no data field.")

    return data, raw_text, payload_json.get("message") or payload_json.get("msg")


def _poll_task_until_complete(
    api_key: str,
    task_id: str,
    poll_interval_s: float,
    timeout_s: int,
    log: bool,
    start_time: float,
) -> tuple[dict[str, Any], str, Any, str | None]:
    interval = poll_interval_s if poll_interval_s > 0 else 1.0
    last_state = None
    last_log_time = start_time

    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed > timeout_s:
            last_state_text = last_state if last_state is not None else "unknown"
            raise RuntimeError(
                f"Task {task_id} timed out after {timeout_s}s (last state={last_state_text}, elapsed={elapsed:.1f}s). "
                "Try increasing timeout or retry."
            )

        data, raw_json, message_field = _fetch_task_record(api_key, task_id)
        state = data.get("state")
        should_log = log and (state != last_state or (now - last_log_time) >= 30.0)
        if should_log:
            _log(log, f"recordInfo response: {raw_json}")
            _log(log, f"Task {task_id} state: {state or 'unknown'} (elapsed={elapsed:.1f}s)")
            last_log_time = now

        last_state = state

        if state == "success":
            return data, raw_json, message_field, f"{elapsed:.1f}s"
        if state == "fail":
            fail_code = data.get("failCode")
            fail_msg = data.get("failMsg") or data.get("msg")
            parts = [f"Task {task_id} failed"]
            if fail_code is not None:
                parts.append(f"failCode={fail_code}")
            if fail_msg:
                parts.append(f"failMsg={fail_msg}")
            if message_field:
                parts.append(f"message={message_field}")
            error_message = "; ".join(parts)

            if _should_retry_fail(fail_code, fail_msg, message_field):
                raise TransientKieError(error_message)

            raise RuntimeError(error_message)

        if should_log:
            _log(log, f"Polling again in {interval} seconds...")
        time.sleep(interval)


def _extract_result_urls(record_data: dict[str, Any]) -> list[str]:
    result_json = record_data.get("resultJson")
    if not result_json:
        raise RuntimeError("Task completed without resultJson.")

    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("resultJson is not valid JSON.") from exc

    result_urls = parsed.get("resultUrls")
    if not result_urls or not isinstance(result_urls, list):
        raise RuntimeError("resultJson does not contain resultUrls.")

    return result_urls


def _download_image(url: str) -> bytes:
    try:
        response = requests.get(url, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download result image: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download result image (status code {response.status_code}).")

    return response.content


def _image_bytes_to_tensor(image_bytes: bytes) -> torch.Tensor:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            rgb_image = img.convert("RGB")
            tensor = torch.frombuffer(rgb_image.tobytes(), dtype=torch.uint8)
            tensor = tensor.view(rgb_image.height, rgb_image.width, 3).float() / 255.0
            return tensor.unsqueeze(0)
    except Exception as exc:
        raise RuntimeError("Failed to decode result image.") from exc


def _image_tensor_to_png_bytes(image: torch.Tensor) -> bytes:
    if image.dim() != 3 or image.shape[2] != 3:
        raise RuntimeError("Image tensor must have shape [H, W, 3].")
    if image.numel() == 0:
        raise RuntimeError("Image tensor is empty.")

    if image.dtype != torch.uint8:
        working = image.detach().cpu().clamp(0, 1) * 255.0
        working = working.round().to(torch.uint8)
    else:
        working = image.detach().cpu()

    working = working.contiguous()
    height, width, _channels = working.shape
    data_bytes = bytes(working.view(-1).tolist())

    try:
        pil_image = Image.frombytes("RGB", (width, height), data_bytes)
    except Exception as exc:
        raise RuntimeError("Failed to convert tensor to image.") from exc

    with BytesIO() as output:
        pil_image.save(output, format="PNG")
        return output.getvalue()


def _should_retry_fail(fail_code: Any, fail_msg: Any, message: Any) -> bool:
    try:
        code_int = int(fail_code)
    except (TypeError, ValueError):
        code_int = None

    if code_int is not None and 500 <= code_int <= 599:
        return True

    combined_text = " ".join(
        str(part).lower()
        for part in (fail_msg, message)
        if isinstance(part, str) and part
    )

    if "internal error" in combined_text or "try again later" in combined_text:
        return True

    return False


def _upload_image(api_key: str, png_bytes: bytes) -> str:
    try:
        response = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("image.png", png_bytes, "image/png")},
            data={"uploadPath": UPLOAD_PATH},
            timeout=120,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to upload image: {exc}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise TransientKieError(
            f"upload returned HTTP {response.status_code}: {response.text}", status_code=response.status_code
        )

    try:
        payload_json: Any = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Upload endpoint did not return valid JSON.") from exc

    success = payload_json.get("success")
    code = payload_json.get("code")
    if not success or code != 200:
        raise RuntimeError(f"Upload failed (code={code}): {payload_json.get('msg')}")

    data = payload_json.get("data") or {}
    url = data.get("downloadUrl")
    if not url:
        raise RuntimeError("Upload response missing downloadUrl.")

    return url


class KIE_GetRemainingCredits:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"log": ("BOOLEAN", {"default": True})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("raw_json", "credits_remaining")
    FUNCTION = "get_remaining_credits"
    CATEGORY = "kie/api"

    def get_remaining_credits(self, log: bool):
        _log(log, "Requesting remaining credits...")
        api_key = _load_api_key()
        raw_json, credits_remaining = _fetch_remaining_credits(api_key)
        _log(log, f"Credits remaining: {credits_remaining}")
        return (raw_json, credits_remaining)


class KIE_NanoBananaPro_Image:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"prompt": ("STRING", {"multiline": True})},
            "optional": {
                "images": ("IMAGE",),
                "aspect_ratio": ("COMBO", {"options": ASPECT_RATIO_OPTIONS, "default": "auto"}),
                "resolution": ("COMBO", {"options": RESOLUTION_OPTIONS, "default": "1K"}),
                "output_format": ("COMBO", {"options": OUTPUT_FORMAT_OPTIONS, "default": "png"}),
                "log": ("BOOLEAN", {"default": True}),
                "poll_interval_s": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 60.0, "step": 0.1}),
                "timeout_s": ("INT", {"default": 300, "min": 1, "max": 3600, "step": 1}),
                "retry_on_fail": ("BOOLEAN", {"default": True}),
                "max_retries": ("INT", {"default": 2, "min": 0, "max": 10, "step": 1}),
                "retry_backoff_s": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 300.0, "step": 0.5}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "kie/api"

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "auto",
        resolution: str = "1K",
        output_format: str = "png",
        log: bool = True,
        poll_interval_s: float = 1.0,
        timeout_s: int = 300,
        retry_on_fail: bool = True,
        max_retries: int = 2,
        retry_backoff_s: float = 3.0,
        images: torch.Tensor | None = None,
    ):
        _validate_prompt(prompt)

        if aspect_ratio not in ASPECT_RATIO_OPTIONS:
            raise RuntimeError("Invalid aspect_ratio. Use the pinned enum options.")
        if resolution not in RESOLUTION_OPTIONS:
            raise RuntimeError("Invalid resolution. Use the pinned enum options.")
        if output_format not in OUTPUT_FORMAT_OPTIONS:
            raise RuntimeError("Invalid output_format. Use the pinned enum options.")

        attempts = max_retries + 1 if retry_on_fail else 1
        attempts = max(attempts, 1)
        backoff = retry_backoff_s if retry_backoff_s >= 0 else 0.0

        for attempt in range(1, attempts + 1):
            start_time = time.time()
            try:
                api_key = _load_api_key()

                image_urls: list[str] = []
                if images is not None:
                    if not isinstance(images, torch.Tensor):
                        raise RuntimeError("images input must be a tensor batch.")
                    if images.dim() != 4 or images.shape[-1] != 3:
                        raise RuntimeError("images input must have shape [B, H, W, 3].")

                    total_images = images.shape[0]
                    if total_images > 8 and log:
                        _log(log, f"More than 8 images provided ({total_images}); only first 8 will be used.")

                    upload_count = min(total_images, 8)
                    if upload_count > 0:
                        _log(log, f"Uploading {upload_count} images...")

                    for idx in range(upload_count):
                        try:
                            png_bytes = _image_tensor_to_png_bytes(images[idx])
                            url = _upload_image(api_key, png_bytes)
                            image_urls.append(url)
                            _log(log, f"Image {idx + 1} upload success: {_truncate_url(url)}")
                        except Exception as exc:
                            _log(log, f"Image {idx + 1} upload failed: {exc}")
                            raise

                payload = {
                    "model": MODEL_NAME,
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        "output_format": output_format,
                        "image_input": image_urls,
                    },
                }

                _log(log, f"Sending {len(image_urls)} image URLs to createTask")

                _log(log, "Creating Nano Banana Pro task...")
                task_id, create_response_text = _create_nano_banana_task(api_key, payload)
                _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
                _log(log, f"Task created with ID {task_id}. Polling for completion...")

                record_data, _raw_json, _message_field, elapsed_text = _poll_task_until_complete(
                    api_key,
                    task_id,
                    poll_interval_s,
                    timeout_s,
                    log,
                    start_time,
                )
                result_urls = _extract_result_urls(record_data)
                _log(log, f"Result URLs: {result_urls}")

                _log(log, f"Downloading result image from {result_urls[0]} (elapsed={elapsed_text})...")
                image_bytes = _download_image(result_urls[0])
                image_tensor = _image_bytes_to_tensor(image_bytes)
                _log(log, "Image downloaded and decoded.")

                _log_remaining_credits(log, record_data, api_key)

                return (image_tensor,)
            except TransientKieError as exc:
                if not retry_on_fail or attempt >= attempts:
                    raise
                _log(log, f"Retrying (attempt {attempt + 1}/{attempts}) after {backoff}s")
                time.sleep(backoff)
                continue


NODE_CLASS_MAPPINGS = {
    "KIE_GetRemainingCredits": KIE_GetRemainingCredits,
    "KIE_NanoBananaPro_Image": KIE_NanoBananaPro_Image,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "KIE_GetRemainingCredits": "KIE Get Remaining Credits",
    "KIE_NanoBananaPro_Image": "KIE Nano Banana Pro (Image)",
}
