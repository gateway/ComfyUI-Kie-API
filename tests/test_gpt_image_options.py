"""Contract regressions; no network calls or ComfyUI imports."""

import unittest

from kie_api.gpt_image_options import build_gpt_image_payload


class GPTImageOptionsTests(unittest.TestCase):
    def payload(self, **overrides):
        args = dict(model="GPT Image 2", mode="text-to-image", prompt="A poster",
                    aspect_ratio="auto", resolution="1K", background="opaque")
        args.update(overrides)
        return build_gpt_image_payload(**args)

    def test_legacy_payload_is_unchanged(self):
        self.assertEqual(self.payload(), {
            "model": "gpt-image-2-text-to-image",
            "input": {"prompt": "A poster", "aspect_ratio": "auto", "resolution": "1K"},
        })

    def test_all_four_new_routes_and_background(self):
        for variant in ("Flare", "Sunburst"):
            for mode in ("text-to-image", "image-to-image"):
                with self.subTest(variant=variant, mode=mode):
                    payload = self.payload(model=f"GPT Image 2.5 {variant}", mode=mode,
                                           resolution="4K", background="transparent")
                    self.assertEqual(payload["model"], f"gpt-image-2-5-{variant.lower()}-{mode}")
                    self.assertEqual(payload["input"]["background"], "transparent")
                    self.assertNotIn("callBackUrl", payload)

    def test_restrictions_are_model_specific(self):
        for ratio, resolution in (("auto", "2K"), ("1:1", "4K"), ("3:2", "1K")):
            with self.subTest(ratio=ratio, resolution=resolution):
                with self.assertRaises(RuntimeError):
                    self.payload(aspect_ratio=ratio, resolution=resolution)
                for variant in ("Flare", "Sunburst"):
                    self.payload(model=f"GPT Image 2.5 {variant}",
                                 aspect_ratio=ratio, resolution=resolution)
        for variant in ("Flare", "Sunburst"):
            for ratio in ("27:16", "16:27", "9:8", "8:9"):
                self.payload(model=f"GPT Image 2.5 {variant}", aspect_ratio=ratio)
                for resolution in ("2K", "4K"):
                    with self.assertRaises(RuntimeError):
                        self.payload(model=f"GPT Image 2.5 {variant}",
                                     aspect_ratio=ratio, resolution=resolution)

    def test_invalid_parameters_fail_closed(self):
        for override in (dict(model="unknown"), dict(mode="edit"), dict(prompt="  "),
                         dict(prompt="a" * 20001), dict(resolution="8K"),
                         dict(background="transparent"), dict(aspect_ratio="5:4")):
            with self.subTest(override=list(override)):
                with self.assertRaises(RuntimeError):
                    self.payload(**override)


if __name__ == "__main__":
    unittest.main()
