"""Contract regressions for the Seedream 5 nodes; no network calls and no ComfyUI imports.

Every entry point is exercised with its network seams patched, so the payload a node
would send is captured and checked without spending credits:

- the create-task helper is replaced by a sentinel exception,
- the API key loader is stubbed and asserted NOT to be called when options are invalid
  (invalid input must fail before any auth or upload),
- the image-to-image entry points get a stubbed uploader.
"""

import unittest
from unittest.mock import patch

import torch

from kie_api import (
    layers,
    seedream5_flash_i2i,
    seedream5_flash_layer,
    seedream5_flash_t2i,
    seedream5_i2i,
    seedream5_lite_i2i,
    seedream5_lite_t2i,
    seedream5_pro_layer,
    seedream5_t2i,
)


RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"]

# (module, entry point, api field carrying the resolution tier, accepted values, model id)
TEXT_TO_IMAGE = [
    (seedream5_t2i, "run_seedream5_pro_text_to_image", "quality", ["basic", "high"], "seedream/5-pro-text-to-image"),
    (seedream5_lite_t2i, "run_seedream5_lite_text_to_image", "quality", ["basic", "high", "ultra"],
     "seedream/5-lite-text-to-image"),
    (seedream5_flash_t2i, "run_seedream5_flash_text_to_image", "size", ["1K", "1.5K", "2K"],
     "seedream/5-flash-text-to-image"),
]

# (module, entry point, api field, accepted values, model id, max reference images)
IMAGE_TO_IMAGE = [
    (seedream5_i2i, "run_seedream5_pro_image_to_image", "quality", ["basic", "high"],
     "seedream/5-pro-image-to-image", 10),
    (seedream5_lite_i2i, "run_seedream5_lite_image_to_image", "quality", ["basic", "high", "ultra"],
     "seedream/5-lite-image-to-image", 14),
    (seedream5_flash_i2i, "run_seedream5_flash_image_to_image", "size", ["1K", "1.5K", "2K"],
     "seedream/5-flash-image-to-image", 10),
]

LAYER_NODES = [
    (seedream5_flash_layer, "run_seedream5_flash_layer_decomposition", "seedream/5-flash-layer-decomposition"),
    (seedream5_pro_layer, "run_seedream5_pro_layer_decomposition", "seedream/5-pro-layer-decomposition"),
]


class _Stop(Exception):
    """Raised where the HTTP call would happen: the payload is already captured."""


def _images(count: int) -> torch.Tensor:
    return torch.zeros((count, 4, 3, 3))


class Seedream5ContractTests(unittest.TestCase):
    @staticmethod
    def _tier(module):
        """The api field that carries the resolution tier, plus a valid default."""
        if hasattr(module, "QUALITY_OPTIONS"):
            return "quality", module.QUALITY_OPTIONS[0]
        return "size", module.SIZE_OPTIONS[0]

    def _t2i_args(self, module, **overrides):
        field, default = self._tier(module)
        args = dict(prompt="A lighthouse at dusk", aspect_ratio="1:1", output_format="png",
                    nsfw_checker=True, poll_interval_s=0, timeout_s=1, log=False)
        args[field] = default
        args.update(overrides)
        return args

    def _i2i_args(self, module, **overrides):
        field, default = self._tier(module)
        args = dict(prompt="Restyle this plate", images=_images(2), aspect_ratio="1:1",
                    output_format="png", nsfw_checker=True, poll_interval_s=0, timeout_s=1, log=False)
        args[field] = default
        args.update(overrides)
        return args

    def captured_t2i_payload(self, module, entry_point, **overrides):
        with patch.object(module, "_load_api_key", return_value="test"), \
             patch.object(module, "_create_seedream_task", side_effect=_Stop) as create:
            with self.assertRaises(_Stop):
                getattr(module, entry_point)(**self._t2i_args(module, **overrides))
        return create.call_args.args[1]

    def captured_i2i_payload(self, module, entry_point, image_count=2, **overrides):
        with patch.object(module, "_load_api_key", return_value="test"), \
             patch.object(module, "_image_tensor_to_png_bytes", return_value=b"png"), \
             patch.object(module, "_upload_image", side_effect=[f"https://ref{i}" for i in range(image_count)]) as upload, \
             patch.object(module, "_create_task", side_effect=_Stop) as create:
            with self.assertRaises(_Stop):
                getattr(module, entry_point)(**self._i2i_args(module, images=_images(image_count), **overrides))
        self.assertEqual(upload.call_count, image_count)
        return create.call_args.args[1]

    # ---- payload shape -------------------------------------------------

    def test_pro_text_to_image_payload(self):
        payload = self.captured_t2i_payload(seedream5_t2i, "run_seedream5_pro_text_to_image", quality="high")
        self.assertEqual(payload, {
            "model": "seedream/5-pro-text-to-image",
            "input": {"prompt": "A lighthouse at dusk", "aspect_ratio": "1:1", "quality": "high",
                      "output_format": "png", "nsfw_checker": True},
        })
        self.assertNotIn("callBackUrl", payload)

    def test_nsfw_checker_and_output_format_reach_the_payload(self):
        for module, entry_point, field, values, _ in TEXT_TO_IMAGE:
            with self.subTest(module=module.__name__):
                payload = self.captured_t2i_payload(module, entry_point, **{field: values[0]},
                                                    output_format="jpeg", nsfw_checker=False)
                self.assertEqual(payload["input"]["output_format"], "jpeg")
                self.assertIs(payload["input"]["nsfw_checker"], False)

    def test_every_text_to_image_tier_and_model_id(self):
        for module, entry_point, field, values, model_id in TEXT_TO_IMAGE:
            for value in values:
                with self.subTest(module=module.__name__, value=value):
                    payload = self.captured_t2i_payload(module, entry_point, **{field: value})
                    self.assertEqual(payload["model"], model_id)
                    self.assertEqual(payload["input"][field], value)

    def test_every_image_to_image_tier_and_references(self):
        for module, entry_point, field, values, model_id, _ in IMAGE_TO_IMAGE:
            for value in values:
                with self.subTest(module=module.__name__, value=value):
                    payload = self.captured_i2i_payload(module, entry_point, **{field: value})
                    self.assertEqual(payload["model"], model_id)
                    self.assertEqual(payload["input"][field], value)
                    self.assertEqual(payload["input"]["image_urls"], ["https://ref0", "https://ref1"])
                    self.assertNotIn("callBackUrl", payload)

    # ---- pinned enums -------------------------------------------------

    def test_every_module_pins_the_same_eight_ratios(self):
        for module, *_ in TEXT_TO_IMAGE + IMAGE_TO_IMAGE:
            with self.subTest(module=module.__name__):
                self.assertEqual(module.ASPECT_RATIO_OPTIONS, RATIOS)
                self.assertIn("21:9", module.ASPECT_RATIO_OPTIONS)

    def test_pro_has_no_ultra_tier_and_lite_does(self):
        self.assertEqual(seedream5_t2i.QUALITY_OPTIONS, ["basic", "high"])
        self.assertEqual(seedream5_lite_t2i.QUALITY_OPTIONS, ["basic", "high", "ultra"])
        with patch.object(seedream5_t2i, "_load_api_key", return_value="test") as auth:
            with self.assertRaises(RuntimeError):
                seedream5_t2i.run_seedream5_pro_text_to_image(
                    **self._t2i_args(seedream5_t2i, quality="ultra"))
            auth.assert_not_called()

    def test_layer_nodes_pin_the_same_tier_options_and_model_ids(self):
        for module, _, model_id in LAYER_NODES:
            with self.subTest(module=module.__name__):
                self.assertEqual(module.SIZE_OPTIONS, ["auto", "1K", "1.5K", "2K"])
                self.assertEqual(module.MODEL_NAME, model_id)
        self.assertEqual(seedream5_flash_layer.SIZE_OPTIONS, seedream5_pro_layer.SIZE_OPTIONS)

    def test_prompt_limits_stay_at_the_documented_values(self):
        for module, *_ in TEXT_TO_IMAGE + IMAGE_TO_IMAGE:
            self.assertEqual(module.PROMPT_MAX_LENGTH, 3000)
        self.assertEqual(seedream5_flash_layer.PROMPT_MAX_LENGTH, 5000)
        self.assertEqual(seedream5_pro_layer.PROMPT_MAX_LENGTH, 5000)

    # ---- fail before auth ---------------------------------------------

    def test_invalid_text_to_image_options_fail_before_auth(self):
        cases = [
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(aspect_ratio="5:4")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(aspect_ratio="21:8")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(quality="medium")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(quality="8K")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(output_format="webp")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(prompt="   ")),
            (seedream5_t2i, "run_seedream5_pro_text_to_image", dict(prompt="a" * 3001)),
            (seedream5_lite_t2i, "run_seedream5_lite_text_to_image", dict(quality="4K")),
            (seedream5_flash_t2i, "run_seedream5_flash_text_to_image", dict(size="4K")),
            (seedream5_flash_t2i, "run_seedream5_flash_text_to_image", dict(size="basic")),
        ]
        for module, entry_point, overrides in cases:
            with self.subTest(module=module.__name__, **overrides):
                with patch.object(module, "_load_api_key", return_value="test") as auth:
                    with self.assertRaises(RuntimeError):
                        getattr(module, entry_point)(**self._t2i_args(module, **overrides))
                    auth.assert_not_called()

    def test_invalid_image_to_image_options_fail_before_auth_or_upload(self):
        cases = [
            (seedream5_i2i, "run_seedream5_pro_image_to_image", dict(aspect_ratio="5:4")),
            (seedream5_i2i, "run_seedream5_pro_image_to_image", dict(quality="ultra")),
            (seedream5_lite_i2i, "run_seedream5_lite_image_to_image", dict(quality="1K")),
            (seedream5_flash_i2i, "run_seedream5_flash_image_to_image", dict(size="4K")),
            (seedream5_i2i, "run_seedream5_pro_image_to_image", dict(prompt="")),
            (seedream5_i2i, "run_seedream5_pro_image_to_image", dict(images=torch.zeros((1, 1, 1, 4)))),
        ]
        for module, entry_point, overrides in cases:
            with self.subTest(module=module.__name__, **overrides):
                with patch.object(module, "_load_api_key", return_value="test") as auth, \
                     patch.object(module, "_upload_image") as upload:
                    with self.assertRaises(RuntimeError):
                        getattr(module, entry_point)(**self._i2i_args(module, **overrides))
                    auth.assert_not_called()
                    upload.assert_not_called()

    def test_reference_count_caps(self):
        for module, entry_point, _, _, _, max_images in IMAGE_TO_IMAGE:
            with self.subTest(module=module.__name__, count=max_images):
                self.captured_i2i_payload(module, entry_point, image_count=max_images)
            with self.subTest(module=module.__name__, count=max_images + 1):
                with patch.object(module, "_load_api_key", return_value="test") as auth, \
                     patch.object(module, "_upload_image") as upload:
                    with self.assertRaises(RuntimeError):
                        getattr(module, entry_point)(
                            **self._i2i_args(module, images=_images(max_images + 1))
                        )
                    auth.assert_not_called()
                    upload.assert_not_called()

    def test_invalid_layer_options_fail_before_auth(self):
        for module, entry_point, _ in LAYER_NODES:
            for overrides in (dict(size="4K"), dict(size="basic"), dict(output_format="webp"),
                              dict(prompt="a" * 5001)):
                with self.subTest(module=module.__name__, **overrides):
                    args = dict(image=_images(1), prompt="", size="1K", output_format="png",
                                poll_interval_s=0, timeout_s=1, log=False)
                    args.update(overrides)
                    with patch.object(layers, "_load_api_key", return_value="test") as auth, \
                         patch.object(layers, "_upload_image") as upload:
                        with self.assertRaises(RuntimeError, msg=overrides):
                            getattr(module, entry_point)(**args)
                        auth.assert_not_called()
                        upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
