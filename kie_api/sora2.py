"""Sora 2 API helpers."""

import json
import time
from typing import Any

import torch

from .auth import _load_api_key
from .credits import _log_remaining_credits
from .jobs import _create_task, _poll_task_until_complete
from .log import _log
from .results import _extract_result_urls
from .upload import _image_tensor_to_png_bytes, _truncate_url, _upload_image
from .validation import _validate_image_tensor_batch, _validate_prompt
from .video import _download_video, _video_bytes_to_comfy_video


def _run_sora2_video(
    model: str,
    prompt: str,
    images: torch.Tensor | None = None,
    aspect_ratio: str = "portrait",
    n_frames: str = "10",
    remove_watermark: bool | None = None,
    upload_method: str = "s3",
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    _validate_prompt(prompt, max_length=2500)
    if aspect_ratio not in ["portrait", "landscape"]:
        raise RuntimeError("Invalid aspect_ratio. Must be 'portrait' or 'landscape'.")
    if n_frames not in ["10", "15"]:
        raise RuntimeError("Invalid n_frames. Must be '10' or '15'.")
    if upload_method not in ["s3", "oss"]:
        raise RuntimeError("Invalid upload_method. Must be 's3' or 'oss'.")

    api_key = _load_api_key()

    input_data = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "n_frames": n_frames,
        "upload_method": upload_method,
    }

    if remove_watermark is not None:
        input_data["remove_watermark"] = remove_watermark

    if images is not None:
        images = _validate_image_tensor_batch(images)
        if images.shape[0] > 1:
            _log(log, f"More than 1 image provided ({images.shape[0]}); only the first will be used.")

        _log(log, f"Uploading source image for {model}...")
        png_bytes = _image_tensor_to_png_bytes(images[0])
        image_url = _upload_image(api_key, png_bytes)
        _log(log, f"Image upload success: {_truncate_url(image_url)}")
        input_data["image_urls"] = [image_url]

    payload = {
        "model": model,
        "input": input_data,
    }

    _log(log, f"Creating {model} task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    result_urls = _extract_result_urls(record_data)
    video_url = result_urls[0]
    _log(log, f"Final video URL: {video_url}")

    video_bytes = _download_video(video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output


def run_sora2_t2v(
    prompt: str,
    aspect_ratio: str,
    n_frames: str,
    remove_watermark: bool,
    upload_method: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    return _run_sora2_video(
        model="sora-2-text-to-video",
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        n_frames=n_frames,
        remove_watermark=remove_watermark,
        upload_method=upload_method,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_sora2_t2v_stable(
    prompt: str,
    aspect_ratio: str,
    n_frames: str,
    upload_method: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    return _run_sora2_video(
        model="sora-2-text-to-video-stable",
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        n_frames=n_frames,
        upload_method=upload_method,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_sora2_i2v(
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    n_frames: str,
    remove_watermark: bool,
    upload_method: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    return _run_sora2_video(
        model="sora-2-image-to-video",
        prompt=prompt,
        images=images,
        aspect_ratio=aspect_ratio,
        n_frames=n_frames,
        remove_watermark=remove_watermark,
        upload_method=upload_method,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_sora2_i2v_stable(
    prompt: str,
    images: torch.Tensor,
    aspect_ratio: str,
    n_frames: str,
    upload_method: str,
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    return _run_sora2_video(
        model="sora-2-image-to-video-stable",
        prompt=prompt,
        images=images,
        aspect_ratio=aspect_ratio,
        n_frames=n_frames,
        upload_method=upload_method,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        log=log,
    )


def run_sora2_characters_pro(
    origin_task_id: str,
    start_time_s: float,
    end_time_s: float,
    character_prompt: str,
    character_user_name: str | None = None,
    safety_instruction: str | None = None,
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> str:
    api_key = _load_api_key()

    if not origin_task_id:
        raise RuntimeError("origin_task_id is required.")
    if not character_prompt:
        raise RuntimeError("character_prompt is required.")

    duration = end_time_s - start_time_s
    if duration < 1.0 or duration > 4.0:
        raise RuntimeError("Selected segment must be 1-4 seconds long.")

    timestamps = f"{start_time_s:.2f},{end_time_s:.2f}"

    input_data = {
        "origin_task_id": origin_task_id,
        "timestamps": timestamps,
        "character_prompt": character_prompt,
    }

    if character_user_name:
        input_data["character_user_name"] = character_user_name
    if safety_instruction:
        input_data["safety_instruction"] = safety_instruction

    payload = {
        "model": "sora-2-characters-pro",
        "input": input_data,
    }

    _log(log, "Creating sora-2-characters-pro task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    result_json_str = record_data.get("resultJson", "")
    if not result_json_str:
        raise RuntimeError("sora-2-characters-pro task completed without resultJson.")

    try:
        result_json = json.loads(result_json_str)
        character_name = result_json.get("characterName")
        if not character_name:
            raise RuntimeError("sora-2-characters-pro resultJson did not contain characterName.")
    except Exception as e:
        raise RuntimeError(f"Failed to parse sora-2-characters-pro resultJson: {e}")

    _log(log, f"Final character handle: {character_name}")
    _log_remaining_credits(log, record_data, api_key, _log)
    return character_name


def run_sora_watermark_remover(
    video_url: str,
    upload_method: str = "s3",
    poll_interval_s: float = 10.0,
    timeout_s: int = 2000,
    log: bool = True,
) -> dict:
    if not video_url:
        raise RuntimeError("video_url is required.")
    if upload_method not in ["s3", "oss"]:
        raise RuntimeError("Invalid upload_method. Must be 's3' or 'oss'.")

    api_key = _load_api_key()

    payload = {
        "model": "sora-watermark-remover",
        "input": {
            "video_url": video_url,
            "upload_method": upload_method,
        },
    }

    _log(log, "Creating sora-watermark-remover task...")
    start_time = time.time()
    task_id, create_response_text = _create_task(api_key, payload)
    _log(log, f"createTask response (elapsed={time.time() - start_time:.1f}s): {create_response_text}")
    _log(log, f"Task created with ID {task_id}. Polling for completion...")

    record_data = _poll_task_until_complete(
        api_key,
        task_id,
        poll_interval_s,
        timeout_s,
        log,
        start_time,
    )

    result_urls = _extract_result_urls(record_data)
    final_video_url = result_urls[0]
    _log(log, f"Final video URL: {final_video_url}")

    video_bytes = _download_video(final_video_url)
    video_output = _video_bytes_to_comfy_video(video_bytes)

    _log_remaining_credits(log, record_data, api_key, _log)
    return video_output
