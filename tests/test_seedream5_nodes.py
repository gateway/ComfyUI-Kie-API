"""Widget vocabulary regressions for the Seedream 5 nodes.

Resolution is offered to the user as a `resolution` combo, which is the convention the
rest of the pack uses (nanobanana2, gpt_image2, seedance2, grok, flux2). The API
happens to call the field `quality` on Pro/Lite and `size` on Flash/Layer, and the
translation must stay in `nodes.py`, so the API vocabulary never reaches the UI.

`nodes.py` uses package-relative imports and cannot be imported as a bare module, so a
synthetic parent package is registered first. Nothing here touches the network.
"""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import patch

import torch


PACK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# class name -> (entry point called by generate(), api field, resolution options, default)
TEXT_TO_IMAGE = {
    "KIE_Seedream5Pro_TextToImage": ("run_seedream5_pro_text_to_image", "quality",
                                     ["1K", "2K"], "1K"),
    "KIE_Seedream5Lite_TextToImage": ("run_seedream5_lite_text_to_image", "quality",
                                      ["2K", "3K", "4K"], "2K"),
    "KIE_Seedream5Flash_TextToImage": ("run_seedream5_flash_text_to_image", "size",
                                       ["1K", "1.5K", "2K"], "1K"),
}

IMAGE_TO_IMAGE = {
    "KIE_Seedream5Pro_ImageToImage": ("run_seedream5_pro_image_to_image", "quality",
                                      ["1K", "2K"], "1K"),
    "KIE_Seedream5Lite_ImageToImage": ("run_seedream5_lite_image_to_image", "quality",
                                       ["2K", "3K", "4K"], "2K"),
    "KIE_Seedream5Flash_ImageToImage": ("run_seedream5_flash_image_to_image", "size",
                                        ["1K", "1.5K", "2K"], "1K"),
}

LAYER_NODES = {
    "KIE_Seedream5Flash_LayerDecomposition": ("run_seedream5_flash_layer_decomposition", ["auto", "1K", "1.5K", "2K"], "auto"),
    "KIE_Seedream5Pro_LayerDecomposition": ("run_seedream5_pro_layer_decomposition", ["auto", "1K", "1.5K", "2K"], "auto"),
}

# the label each tier must turn into, per node: the same "2K" is `high` on Pro but
# `basic` on Lite, so the expectation cannot be keyed by the label alone
EXPECTED_API_VALUE = {
    "KIE_Seedream5Pro_TextToImage": {"1K": "basic", "2K": "high"},
    "KIE_Seedream5Lite_TextToImage": {"2K": "basic", "3K": "high", "4K": "ultra"},
    "KIE_Seedream5Flash_TextToImage": {"1K": "1K", "1.5K": "1.5K", "2K": "2K"},
    "KIE_Seedream5Pro_ImageToImage": {"1K": "basic", "2K": "high"},
    "KIE_Seedream5Lite_ImageToImage": {"2K": "basic", "3K": "high", "4K": "ultra"},
    "KIE_Seedream5Flash_ImageToImage": {"1K": "1K", "1.5K": "1.5K", "2K": "2K"},
    "KIE_Seedream5Flash_LayerDecomposition": {"auto": "auto", "1K": "1K", "1.5K": "1.5K", "2K": "2K"},
    "KIE_Seedream5Pro_LayerDecomposition": {"auto": "auto", "1K": "1K", "1.5K": "1.5K", "2K": "2K"},
}


def _load_nodes():
    if "kiepack" not in sys.modules:
        package = types.ModuleType("kiepack")
        package.__path__ = [PACK_ROOT]
        sys.modules["kiepack"] = package
    if "kiepack.nodes" in sys.modules:
        return sys.modules["kiepack.nodes"]
    spec = importlib.util.spec_from_file_location("kiepack.nodes", os.path.join(PACK_ROOT, "nodes.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["kiepack.nodes"] = module
    spec.loader.exec_module(module)
    return module


NODES = _load_nodes()


class Seedream5WidgetTests(unittest.TestCase):
    def widgets(self, class_name):
        node_class = getattr(NODES, class_name)
        definition = node_class.INPUT_TYPES()
        return {**definition.get("required", {}), **definition.get("optional", {})}

    def test_all_eight_nodes_expose_a_resolution_combo(self):
        for class_name, (_, field, options, default) in {**TEXT_TO_IMAGE, **IMAGE_TO_IMAGE}.items():
            with self.subTest(node=class_name):
                widgets = self.widgets(class_name)
                self.assertIn("resolution", widgets)
                self.assertEqual(list(widgets["resolution"][1]["options"]), options)
                self.assertEqual(widgets["resolution"][1]["default"], default)
                self.assertEqual(widgets["resolution"][0], "COMBO")

    def test_layer_nodes_expose_the_same_tier_options(self):
        for class_name, (_, options, default) in LAYER_NODES.items():
            with self.subTest(node=class_name):
                widgets = self.widgets(class_name)
                self.assertEqual(list(widgets["resolution"][1]["options"]), options)
                self.assertEqual(widgets["resolution"][1]["default"], default)

    def test_no_node_leaks_the_api_field_names_into_the_ui(self):
        for class_name in list(TEXT_TO_IMAGE) + list(IMAGE_TO_IMAGE) + list(LAYER_NODES):
            with self.subTest(node=class_name):
                widgets = self.widgets(class_name)
                self.assertNotIn("quality", widgets)
                self.assertNotIn("size", widgets)

    def test_every_offered_tier_has_a_translation(self):
        for class_name in list(TEXT_TO_IMAGE) + list(IMAGE_TO_IMAGE) + list(LAYER_NODES):
            with self.subTest(node=class_name):
                options = list(self.widgets(class_name)["resolution"][1]["options"])
                self.assertEqual(sorted(EXPECTED_API_VALUE[class_name]), sorted(options))

    def test_generate_translates_the_label_into_the_api_value(self):
        cases = [
            ("KIE_Seedream5Pro_TextToImage", dict(prompt="A poster"), "quality"),
            ("KIE_Seedream5Lite_TextToImage", dict(prompt="A poster"), "quality"),
            ("KIE_Seedream5Flash_TextToImage", dict(prompt="A poster"), "size"),
            ("KIE_Seedream5Pro_ImageToImage", dict(prompt="Edit", images=torch.zeros((1, 4, 3, 3))), "quality"),
            ("KIE_Seedream5Lite_ImageToImage", dict(prompt="Edit", images=torch.zeros((1, 4, 3, 3))), "quality"),
            ("KIE_Seedream5Flash_ImageToImage", dict(prompt="Edit", images=torch.zeros((1, 4, 3, 3))), "size"),
        ]
        for class_name, extra, field in cases:
            options = self.widgets(class_name)["resolution"][1]["options"]
            for resolution in options:
                with self.subTest(node=class_name, resolution=resolution):
                    node_class = getattr(NODES, class_name)
                    entry_point = node_class.FUNCTION
                    target = {**TEXT_TO_IMAGE, **IMAGE_TO_IMAGE}[class_name][0]
                    with patch.object(NODES, target, return_value=torch.zeros((1, 2, 2, 3))) as runner:
                        result = getattr(node_class(), entry_point)(resolution=resolution, log=False, **extra)
                    self.assertEqual(tuple(result[0].shape), (1, 2, 2, 3))
                    self.assertEqual(runner.call_args.kwargs[field], EXPECTED_API_VALUE[class_name][resolution])
                    self.assertNotIn("resolution", runner.call_args.kwargs)

    def test_layer_nodes_pass_the_tier_and_return_three_batches(self):
        for class_name, (target, options, _) in LAYER_NODES.items():
            for resolution in options:
                with self.subTest(node=class_name, resolution=resolution):
                    node_class = getattr(NODES, class_name)
                    stub = (torch.zeros((2, 2, 2, 3)), torch.zeros((2, 2, 2)), "[]")
                    with patch.object(NODES, target, return_value=stub) as runner:
                        result = getattr(node_class(), node_class.FUNCTION)(
                            image=torch.zeros((1, 4, 3, 3)), resolution=resolution, log=False)
                    self.assertEqual(len(result), 3)
                    self.assertEqual(runner.call_args.kwargs["size"], resolution)
                    self.assertNotIn("resolution", runner.call_args.kwargs)
                    self.assertEqual(runner.call_args.kwargs["image"].shape, (1, 4, 3, 3))


if __name__ == "__main__":
    unittest.main()
