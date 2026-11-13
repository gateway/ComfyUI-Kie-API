"""Windows-only checks against the real ComfyUI V3 API; no provider calls."""
import importlib
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COMFY_ROOT = ROOT.parent.parent
if (COMFY_ROOT / "comfy_api").is_dir():
    sys.path.insert(0, str(COMFY_ROOT))

from comfy_api.latest import io
from comfy_api.latest._io import get_finalized_class_inputs, build_nested_inputs


class NativeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the native module without importing unrelated nodes in the pack.
        cls.package = "_kie_native_test_pack"
        package = types.ModuleType(cls.package)
        package.__path__ = [str(ROOT)]
        sys.modules[cls.package] = package
        name = cls.package + ".gpt_image_nodes"
        spec = importlib.util.spec_from_file_location(name, ROOT / "gpt_image_nodes.py")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[name] = cls.module
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        for key in list(sys.modules):
            if key == cls.package or key.startswith(cls.package + "."):
                del sys.modules[key]

    def test_real_schemas_validate_and_preserve_output_slots(self):
        for node in (self.module.KIE_GPTImage_TextToImage, self.module.KIE_GPTImage_ImageToImage):
            schema = node.GET_SCHEMA()
            self.assertEqual([o.io_type for o in schema.outputs], ["IMAGE", "MASK", "STRING", "STRING", "STRING"])
            self.assertEqual(node.GET_NODE_INFO_V1()["input"]["required"]["model"][0], "COMFY_DYNAMICCOMBO_V3")

    def test_comfy_parser_produces_the_expected_nested_request(self):
        node = self.module.KIE_GPTImage_TextToImage
        values = {
            "prompt": "A small looping icon", "log": False,
            "model": "GPT Image 2.6 Flare", "model.output": "GIF",
            "model.quality": "medium", "model.complexity": "high", "model.moderation": "low",
            "model.output.background": "opaque", "model.output.frame_count": "9",
            "model.output.frame_duration_ms": 200, "model.output.gif_size": "512x512",
        }
        _, _, paths = get_finalized_class_inputs(node.INPUT_TYPES(), values)
        nested = build_nested_inputs(values, paths)
        helpers = importlib.import_module(self.package + ".kie_api.gpt_image2")
        with patch.object(helpers, "run_gpt_image2_text_to_image", return_value=(None, None, "[]", "", "{}")) as run:
            result = node.execute(**nested)
        self.assertIsInstance(result, io.NodeOutput)
        self.assertEqual(len(result.result), 5)
        self.assertEqual(run.call_args.kwargs["output_format"], "gif")
        self.assertEqual(run.call_args.kwargs["gif_size"], "512x512")
        self.assertEqual(run.call_args.kwargs["model"], "GPT Image 2.6 Flare")

    def test_native_svg_edit_does_not_expose_a_mask_branch(self):
        node = self.module.KIE_GPTImage_ImageToImage
        values = {"model": "GPT Image 2.6 Sunburst", "model.output": "SVG",
                  "model.output.aspect": "auto", "model.output.edit_guide": "Markup"}
        inputs, _, _ = get_finalized_class_inputs(node.INPUT_TYPES(), values)
        self.assertIn("model.output.edit_guide.markup", inputs["required"])
        self.assertNotIn("model.output.edit_guide.mask", inputs["required"])
        self.assertNotIn("model.output.frame_count", inputs["required"])


if __name__ == "__main__":
    unittest.main()
