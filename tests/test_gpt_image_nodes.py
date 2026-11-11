"""Inspect node schemas without importing torch or the ComfyUI runtime."""
import ast
from pathlib import Path
import unittest
from kie_api import gpt_image_options as options


class GPTImageNodeSchemaTests(unittest.TestCase):
    def schemas(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / "nodes.py").read_text())
        namespace = dict(
            GPT_IMAGE2_ASPECT_RATIO_OPTIONS=options.ASPECT_RATIO_OPTIONS,
            GPT_IMAGE2_RESOLUTION_OPTIONS=options.RESOLUTION_OPTIONS,
            GPT_IMAGE_MODEL_OPTIONS=options.MODEL_OPTIONS,
            GPT_IMAGE_DEFAULT_MODEL=options.DEFAULT_MODEL,
            GPT_IMAGE_BACKGROUND_OPTIONS=options.BACKGROUND_OPTIONS,
            gpt_image_widget_options=options.model_widget_options,
            gpt_image_generation_widgets=options.generation_widgets,
        )
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef) or cls.name not in ("KIE_GPTImage2_TextToImage", "KIE_GPTImage2_ImageToImage"):
                continue
            method = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "INPUT_TYPES")
            method.decorator_list = []
            exec(compile(ast.Module(body=[method], type_ignores=[]), "node-schema", "exec"), namespace)
            constants = {item.targets[0].id: ast.literal_eval(item.value) for item in cls.body
                         if isinstance(item, ast.Assign) and item.targets[0].id in ("RETURN_TYPES", "RETURN_NAMES")}
            yield cls.name, namespace["INPUT_TYPES"](None), constants

    def test_old_widget_and_output_order_preserved(self):
        for name, schema, constants in self.schemas():
            self.assertEqual(list(schema["optional"])[:5], ["aspect_ratio", "resolution", "log", "model", "background"])
            self.assertEqual(constants["RETURN_TYPES"], ("IMAGE", "MASK", "STRING", "STRING", "STRING"))
            self.assertEqual(constants["RETURN_NAMES"][:2], ("image", "mask"))
            self.assertEqual(schema["optional"]["model"][1]["default"], "GPT Image 2")

    def test_mode_specific_economy_formats_and_typed_edit_guides(self):
        for name, schema, _ in self.schemas():
            rules = schema["optional"]["model"][1]["kie_model_options"]
            if name.endswith("ImageToImage"):
                self.assertEqual(rules["GPT Image 2.6 Economy"]["formats"], ["png"])
                self.assertEqual(schema["optional"]["mask"][0], "MASK")
                self.assertEqual(schema["optional"]["markup"][0], "IMAGE")
                self.assertEqual(schema["optional"]["markup_mask"][0], "MASK")
            else:
                self.assertEqual(rules["GPT Image 2.6 Economy"]["formats"], ["png", "gif"])
                self.assertNotIn("mask", schema["optional"])


if __name__ == "__main__":
    unittest.main()
