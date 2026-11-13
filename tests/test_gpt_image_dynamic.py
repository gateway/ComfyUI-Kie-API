"""Dependency-free native-schema structure and request translation tests.

The IO recorder below does not simulate ComfyUI rendering or execution. Windows
runtime tests separately validate against the real ComfyUI schema implementation.
"""
from types import SimpleNamespace
import unittest

from kie_api.gpt_image_dynamic import model_input, request_options
from kie_api.gpt_image_options import build_gpt_image_payload


class Input:
    def __init__(self, id, **kwargs):
        self.id = id
        self.__dict__.update(kwargs)


class Option:
    def __init__(self, key, inputs):
        self.key, self.inputs = key, inputs


IO = SimpleNamespace(**{name: SimpleNamespace(Input=Input) for name in
                         ("Combo", "Int", "String", "Image", "Mask", "Boolean")},
                     DynamicCombo=SimpleNamespace(Input=Input, Option=Option))


def branch(widget, key):
    return next(option for option in widget.options if option.key == key)


def field(fields, name):
    return next(item for item in fields if item.id == name)


def defaults(fields):
    result = {}
    for item in fields:
        if getattr(item, "options", None) and isinstance(item.options[0], Option):
            choice = item.options[0]
            result[item.id] = {item.id: choice.key, **defaults(choice.inputs)}
        else:
            result[item.id] = getattr(item, "default", None)
    return result


class NativeGPTImageTests(unittest.TestCase):
    def selection(self, model="GPT Image 2.6 Flare", kind="Image", mode="text-to-image"):
        model_branch = branch(model_input(IO, mode), model)
        selected = {"model": model, **defaults(model_branch.inputs)}
        output = branch(field(model_branch.inputs, "output"), kind)
        selected["output"] = {"output": kind, **defaults(output.inputs)}
        return selected, output.inputs

    def test_all_exposed_model_and_output_defaults_build_valid_payloads(self):
        for mode in ("text-to-image", "image-to-image"):
            for model in model_input(IO, mode).options:
                for output in field(model.inputs, "output").options:
                    with self.subTest(model=model.key, mode=mode, output=output.key):
                        selection, _ = self.selection(model.key, output.key, mode)
                        args = request_options("A poster", selection, mode)
                        payload = build_gpt_image_payload(prompt="A poster", mode=mode, **args)
                        self.assertTrue(payload["model"].endswith(mode))

    def test_only_relevant_fields_exist_in_each_branch(self):
        for kind in ("Image", "SVG", "GIF"):
            _, fields = self.selection(kind=kind)
            names = {item.id for item in fields}
            self.assertEqual("aspect" in names, kind != "GIF")
            self.assertEqual("format" in names, kind == "Image")
            self.assertEqual("svg_model" in names, kind == "SVG")
            self.assertEqual("frame_count" in names, kind == "GIF")
            self.assertEqual("gif_size" in names, kind == "GIF")
        _, fields = self.selection()
        formats = field(fields, "format")
        for fmt in formats.options:
            names = {item.id for item in fmt.inputs}
            self.assertEqual("output_compression" in names, fmt.key in ("jpeg", "webp"))
            if fmt.key == "jpeg":
                self.assertEqual(field(fmt.inputs, "background").options, ["opaque"])

    def test_economy_and_old_models_hide_unsupported_controls(self):
        for mode in ("text-to-image", "image-to-image"):
            models = model_input(IO, mode)
            for name in ("GPT Image 2", "GPT Image 2.5 Flare", "GPT Image 2.6 Economy"):
                model = branch(models, name)
                self.assertNotIn("quality", {item.id for item in model.inputs})
                outputs = field(model.inputs, "output").options
                expected = ["Image", "GIF"] if name.endswith("Economy") and mode == "text-to-image" else ["Image"]
                self.assertEqual([option.key for option in outputs], expected)
                for output in outputs:
                    self.assertNotIn("edit_guide", {item.id for item in output.inputs})

    def test_masks_only_available_for_raster_edits(self):
        for kind in ("Image", "SVG", "GIF"):
            selection, fields = self.selection(kind=kind, mode="image-to-image")
            guides = field(fields, "edit_guide").options
            self.assertEqual([item.key for item in guides], ["None", "Mask", "Markup"] if kind == "Image" else ["None", "Markup"])
            selection["output"]["edit_guide"] = {"edit_guide": "Markup", "markup": "image", "markup_mask": "alpha"}
            args = request_options("Edit", selection, "image-to-image")
            self.assertEqual(args["markup"], "image")
            self.assertEqual(args["markup_mask"], "alpha")

    def test_branch_translation_ignores_stale_inactive_fields(self):
        selection, _ = self.selection(kind="GIF")
        selection["output"].update(aspect={"aspect": "bad", "resolution": "bad"}, svg_model="bad", format={"format": "svg"})
        args = request_options("Animate", selection, "text-to-image")
        self.assertEqual(args["output_format"], "gif")
        self.assertEqual(args["aspect_ratio"], "auto")
        self.assertNotIn("svg_model", args)
        selection, _ = self.selection(mode="image-to-image")
        selection["output"]["edit_guide"] = {"edit_guide": "None", "mask": "stale"}
        self.assertNotIn("mask", request_options("Edit", selection, "image-to-image"))

    def test_invalid_connected_or_api_values_fail_before_runtime(self):
        for kind, mutate in (
            ("Image", lambda x: x.update(quality="wrong")),
            ("GIF", lambda x: x["output"].update(frame_duration_ms=21)),
            ("SVG", lambda x: x["output"].update(svg_model="wrong")),
            ("GIF", lambda x: x["output"].update(edit_guide={"edit_guide": "Mask", "mask": "x"})),
            ("Image", lambda x: x["output"].update(edit_guide={"edit_guide": "Markup", "markup": "x"})),
        ):
            selection, _ = self.selection(kind=kind, mode="image-to-image")
            mutate(selection)
            with self.assertRaises(RuntimeError):
                request_options("Edit", selection, "image-to-image")
        for invalid in (None, "GPT Image 2.6 Flare", {}, {"model": "unknown"}):
            with self.assertRaises(RuntimeError):
                request_options("Edit", invalid, "text-to-image")

    def test_resolution_choices_match_legacy_contract(self):
        _, fields = self.selection(model="GPT Image 2")
        ratios = field(fields, "aspect")
        self.assertEqual(field(branch(ratios, "auto").inputs, "resolution").options, ["1K"])
        self.assertEqual(field(branch(ratios, "1:1").inputs, "resolution").options, ["1K", "2K"])
        _, fields = self.selection(model="GPT Image 2.5 Flare")
        self.assertEqual(field(branch(field(fields, "aspect"), "27:16").inputs, "resolution").options, ["1K"])


if __name__ == "__main__":
    unittest.main()
