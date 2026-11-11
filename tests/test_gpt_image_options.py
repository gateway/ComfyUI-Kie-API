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


class GPTImage26OptionsTests(unittest.TestCase):
    def payload(self, **overrides):
        args = dict(model="GPT Image 2.6 Flare", mode="text-to-image", prompt="A poster",
                    aspect_ratio="auto", resolution="1K", background="opaque")
        args.update(overrides)
        return build_gpt_image_payload(**args)

    def test_six_routes_and_economy_omissions(self):
        for variant in ("Flare", "Sunburst", "Economy"):
            for mode in ("text-to-image", "image-to-image"):
                result = self.payload(model=f"GPT Image 2.6 {variant}", mode=mode)
                self.assertEqual(result["model"], f"gpt-image-2-6/{variant.lower()}-{mode}")
                if variant == "Economy":
                    self.assertEqual(set(result["input"]), {"prompt", "aspect_ratio", "background", "output_format"})
                else:
                    self.assertEqual(result["input"]["quality"], "medium")

    def test_limits_do_not_leak_between_versions(self):
        self.payload(prompt="a" * 32000, aspect_ratio="5:4", resolution="4K")
        for changes in (dict(prompt="a" * 32001), dict(aspect_ratio="27:16"),
                        dict(model="GPT Image 2.6 Economy", prompt="a" * 20001),
                        dict(model="GPT Image 2.6 Economy", resolution="2K"),
                        dict(model="GPT Image 2.6 Economy", mode="image-to-image", output_format="gif")):
            with self.subTest(changes=changes.keys()), self.assertRaises(RuntimeError):
                self.payload(**changes)

    def test_gif_types_and_budget(self):
        result = self.payload(output_format="gif", gif_size="512x512", frame_count="16")
        self.assertEqual(result["input"]["frame_count"], 16)
        self.assertNotIn("resolution", result["input"])
        self.assertNotIn("aspect_ratio", result["input"])
        result = self.payload(model="GPT Image 2.6 Economy", output_format="gif", frame_count="64")
        self.assertEqual(result["input"]["frame_count"], "64")
        self.assertNotIn("size", result["input"])
        for overrides in (dict(gif_size="1024x1024", frame_count="2"),
                          dict(gif_size="768x768", frame_count="16"),
                          dict(gif_size="1:1"), dict(frame_count="64"),
                          dict(frame_duration_ms=21), dict(frame_duration_ms=True)):
            with self.subTest(overrides=overrides), self.assertRaises(RuntimeError):
                self.payload(output_format="gif", **overrides)

    def test_inactive_values_are_not_sent(self):
        result = self.payload(frame_count="garbage", gif_size="garbage", svg_model="garbage")
        for name in ("frame_count", "size", "svg", "output_compression"):
            self.assertNotIn(name, result["input"])
        result = self.payload(output_format="svg")
        self.assertEqual(result["input"]["svg"], {"model": "gpt-5.6-luna"})
        result = self.payload(output_format="webp", output_compression=70)
        self.assertEqual(result["input"]["output_compression"], 70)
        with self.assertRaises(RuntimeError):
            self.payload(output_format="jpeg", background="transparent")

    def test_edit_gif_omits_unverified_size_field(self):
        result = self.payload(mode="image-to-image", output_format="gif", gif_size="bad")
        self.assertNotIn("size", result["input"])


if __name__ == "__main__":
    unittest.main()
