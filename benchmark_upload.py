import time
import torch
import concurrent.futures
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

import kie_api.nanobanana as nb

# Global vars to track mock uploads
uploaded_urls = []
should_fail_on_index = -1

# Mock _upload_image to simulate network latency
def mock_upload_image(api_key, png_bytes):
    # Determine which image this is by reading the mock png_bytes
    idx = int(png_bytes.decode('utf-8').split('_')[1])

    if idx == should_fail_on_index:
        raise RuntimeError(f"Simulated network error on index {idx}")

    time.sleep(0.5)  # Simulate 500ms upload time
    url = f"https://example.com/uploaded_{idx}.png"
    uploaded_urls.append(url)
    return url

def mock_image_tensor_to_png_bytes(tensor):
    # The tensor mock has shape (100, 100, 3) and values set to the index
    idx = int(tensor[0, 0, 0].item())
    return f"fake_{idx}_data".encode('utf-8')

def mock_load_api_key():
    return "fake_key"

def mock_create_nano_banana_task(api_key, payload):
    return "fake_task_id", "{}"

def mock_poll_task_until_complete(*args, **kwargs):
    return {}

# Capture the payload sent to create_nano_banana_task
captured_payload = {}

def mock_create_nano_banana_task(api_key, payload):
    global captured_payload
    captured_payload = payload
    return "fake_task_id", "{}"

def mock_poll_task_until_complete(*args, **kwargs):
    return {}

def mock_extract_result_urls(record_data):
    return ["https://example.com/result.png"]

def mock_download_image(url):
    return b"fake_image_bytes"

def mock_image_bytes_to_tensor(bytes_data):
    return torch.zeros((1, 100, 100, 3))

def mock_log_remaining_credits(*args, **kwargs):
    pass

@patch('kie_api.nanobanana._upload_image', side_effect=mock_upload_image)
@patch('kie_api.nanobanana._image_tensor_to_png_bytes', side_effect=mock_image_tensor_to_png_bytes)
@patch('kie_api.nanobanana._load_api_key', side_effect=mock_load_api_key)
@patch('kie_api.nanobanana._create_nano_banana_task', side_effect=mock_create_nano_banana_task)
@patch('kie_api.nanobanana._poll_task_until_complete', side_effect=mock_poll_task_until_complete)
@patch('kie_api.nanobanana._extract_result_urls', side_effect=mock_extract_result_urls)
@patch('kie_api.nanobanana._download_image', side_effect=mock_download_image)
@patch('kie_api.nanobanana._image_bytes_to_tensor', side_effect=mock_image_bytes_to_tensor)
@patch('kie_api.nanobanana._log_remaining_credits', side_effect=mock_log_remaining_credits)
def run_benchmark(*args):
    global uploaded_urls, should_fail_on_index, captured_payload

    print("--- Testing Success Case ---")
    # Create 8 fake images
    images = torch.zeros((8, 100, 100, 3))
    # Give them unique values to track order
    for i in range(8):
        images[i, :, :, :] = i

    start_time = time.time()
    try:
        nb.run_nanobanana_image_job(
            prompt="test",
            images=images,
            log=False
        )
    except Exception as e:
        print(f"Error during benchmark: {e}")
    end_time = time.time()

    duration = end_time - start_time
    print(f"Time taken for 8 images: {duration:.4f} seconds")

    # Assert performance improvement
    assert duration < 1.0, f"Benchmark took too long! expected < 1.0s, got {duration:.4f}s"
    print("Performance improvement verified! (>4s -> <1s)")

    # Assert correct ordering in payload
    expected_urls = [f"https://example.com/uploaded_{i}.png" for i in range(8)]
    payload_urls = captured_payload['input']['image_input']
    assert payload_urls == expected_urls, f"URL Order mismatch! Expected {expected_urls}, got {payload_urls}"
    print("URL ordering verified!")


    print("\n--- Testing Exception Propagation ---")
    uploaded_urls = []
    should_fail_on_index = 4
    exception_caught = False

    try:
        nb.run_nanobanana_image_job(
            prompt="test_fail",
            images=images,
            log=False,
            retry_on_fail=False # Disable retry to fail fast
        )
    except Exception as e:
        exception_caught = True
        print(f"Successfully caught expected exception: {e}")
        assert "Simulated network error on index 4" in str(e), f"Unexpected exception message: {e}"

    assert exception_caught, "Expected exception was not raised!"
    print("Exception propagation verified!")


if __name__ == "__main__":
    run_benchmark()
