"""Layer-decomposition assembly regressions; no network calls, local fixtures only.

The real endpoints are guarded by a credit reserve (base + up to 16 layers), so the
network is replaced by in-memory fixtures that mirror the shape of a KIE response:
a base image plus two layers, each delivered LARGER than its bounding box (as KIE
does), which also covers the resize-into-box path.

Checked here: canvas/box placement, the inverse-alpha mask convention of the pack
(1.0 = transparent), the per-layer report, and the metadata-less Flash fallback
(only `resultUrls`, so plates are passed through full canvas).
"""

import json
import unittest
from io import BytesIO
from unittest.mock import patch

import torch
from PIL import Image

from kie_api import layers, seedream5_flash_layer, seedream5_pro_layer


BASE_SIZE = (160, 100)          # width, height of the base image
TITLE_BOX = (10, 8, 90, 28)     # left, top, right, bottom
OBJECT_BOX = (100, 30, 150, 92)
DELIVERED_SCALE = 1.5           # layers arrive bigger than their box
TITLE_RGBA = (240, 196, 90, 128)
OBJECT_RGBA = (90, 160, 240, 255)


def _png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _plate(box, rgba, scale=DELIVERED_SCALE) -> bytes:
    width = int((box[2] - box[0]) * scale)
    height = int((box[3] - box[1]) * scale)
    return _png(Image.new("RGBA", (width, height), rgba))


def _base_plate() -> bytes:
    return _png(Image.new("RGBA", BASE_SIZE, (18, 22, 34, 255)))


def _record(layers_data, urls):
    parsed = {"resultUrls": list(urls)}
    if layers_data is not None:
        parsed["resultObject"] = {"layers_data": layers_data}
    return {"resultJson": json.dumps(parsed), "creditsConsumed": 0}


def _layout(base_url="fixture://base", title_url="fixture://title", object_url="fixture://object"):
    return [
        {"z_index": 0, "size": f"{BASE_SIZE[0]}x{BASE_SIZE[1]}", "output_format": "jpeg", "url": base_url},
        {
            "z_index": 1,
            "size": f"{int((TITLE_BOX[2] - TITLE_BOX[0]) * DELIVERED_SCALE)}x{int((TITLE_BOX[3] - TITLE_BOX[1]) * DELIVERED_SCALE)}",
            "output_format": "png",
            "bounding_box": {"absolute": list(TITLE_BOX)},
            "name": "Seedream Title Text",
            "description": "Fixture title bar.",
            "url": title_url,
        },
        {
            "z_index": 2,
            "size": f"{int((OBJECT_BOX[2] - OBJECT_BOX[0]) * DELIVERED_SCALE)}x{int((OBJECT_BOX[3] - OBJECT_BOX[1]) * DELIVERED_SCALE)}",
            "output_format": "png",
            "bounding_box": {"absolute": list(OBJECT_BOX)},
            "name": "Golden Disc",
            "description": "Fixture object.",
            "url": object_url,
        },
    ]


def _fixtures():
    return {
        "fixture://base": _base_plate(),
        "fixture://title": _plate(TITLE_BOX, TITLE_RGBA),
        "fixture://object": _plate(OBJECT_BOX, OBJECT_RGBA),
    }


class LayerAssemblyTests(unittest.TestCase):
    def run_layers(self, module, record, fixtures, image=None, **overrides):
        args = dict(model_name=module.MODEL_NAME, size_options=module.SIZE_OPTIONS,
                    image=image if image is not None else torch.zeros((1, 4, 3, 3)),
                    prompt="", size="1K", output_format="png", poll_interval_s=0, timeout_s=1, log=False)
        args.update(overrides)
        with patch.object(layers, "_load_api_key", return_value="test"), \
             patch.object(layers, "_upload_image", return_value="fixture://upload"), \
             patch.object(layers, "_image_tensor_to_png_bytes", return_value=b"png"), \
             patch.object(layers, "_create_task", return_value=("fixture-task", "{}")) as create, \
             patch.object(layers, "_poll_task_until_complete", return_value=record), \
             patch.object(layers, "_download_image", side_effect=lambda url: fixtures[url]):
            result = layers.run_layer_decomposition(**args)
        return result, create.call_args.args[1]

    def test_layers_are_placed_on_their_bounding_box_with_inverse_alpha_masks(self):
        images, masks, layer_info = self.run_layers(seedream5_flash_layer, _record(_layout(), ["fixture://base"]),
                                                    _fixtures())[0]
        report = json.loads(layer_info)

        self.assertEqual(tuple(images.shape), (3, BASE_SIZE[1], BASE_SIZE[0], 3))
        self.assertEqual(tuple(masks.shape), (3, BASE_SIZE[1], BASE_SIZE[0]))
        self.assertEqual(images.dtype, torch.float32)

        # the opaque base fills the canvas and yields an all-zero mask
        self.assertEqual(float(masks[0].sum()), 0.0)
        self.assertEqual(report[0]["origin"], [0, 0])
        self.assertEqual(report[0]["size"], list(BASE_SIZE))

        # report keeps z_index order, names and the box the layer was placed in
        self.assertEqual([entry["z_index"] for entry in report], [0, 1, 2])
        self.assertEqual(report[1]["name"], "Seedream Title Text")
        self.assertEqual(report[1]["origin"], [TITLE_BOX[0], TITLE_BOX[1]])
        self.assertEqual(report[1]["size"], [TITLE_BOX[2] - TITLE_BOX[0], TITLE_BOX[3] - TITLE_BOX[1]])

        # the title plate arrived 1.5x its box: it must be resized into the box, colour preserved
        self.assertAlmostEqual(float(images[1][TITLE_BOX[1] + 10, TITLE_BOX[0] + 40, 0]), TITLE_RGBA[0] / 255.0, places=2)
        self.assertAlmostEqual(float(images[1][TITLE_BOX[1] + 10, TITLE_BOX[0] + 40, 2]), TITLE_RGBA[2] / 255.0, places=2)

        # mask is 1 - alpha: 128/255 inside the box, fully transparent elsewhere
        inside_title = masks[1][TITLE_BOX[1]:TITLE_BOX[3], TITLE_BOX[0]:TITLE_BOX[2]]
        self.assertAlmostEqual(float(inside_title.mean()), 1.0 - 128 / 255, places=5)

        # fully opaque object layer: mask 0 inside its box, 1 outside
        left, top, right, bottom = OBJECT_BOX
        inside_object = masks[2][top:bottom, left:right]
        self.assertAlmostEqual(float(inside_object.mean()), 0.0, places=5)
        outside = (float(masks[2].sum()) - float(inside_object.sum())) / (masks[2].numel() - inside_object.numel())
        self.assertAlmostEqual(outside, 1.0, places=5)

        # nothing leaks outside the boxes
        self.assertAlmostEqual(float(masks[2][:, :left].mean()), 1.0, places=5)
        self.assertAlmostEqual(float(masks[1][:, TITLE_BOX[2]:].mean()), 1.0, places=5)

    def test_payload_and_model_name_are_passed_through(self):
        _, payload = self.run_layers(seedream5_pro_layer, _record(_layout(), ["fixture://base"]), _fixtures(),
                                     prompt="Split the poster", size="2K", output_format="jpeg")
        self.assertEqual(payload["model"], "seedream/5-pro-layer-decomposition")
        self.assertEqual(payload["input"]["prompt"], "Split the poster")
        self.assertEqual(payload["input"]["size"], "2K")
        self.assertEqual(payload["input"]["output_format"], "jpeg")
        self.assertEqual(payload["input"]["image_url"], "fixture://upload")

    def test_without_a_prompt_the_prompt_key_is_omitted(self):
        _, payload = self.run_layers(seedream5_flash_layer, _record(_layout(), ["fixture://base"]), _fixtures())
        self.assertNotIn("prompt", payload["input"])

    def test_metadata_less_flash_result_is_handed_over_full_canvas(self):
        urls = ["fixture://base", "fixture://title"]
        images, masks, layer_info = self.run_layers(seedream5_flash_layer, _record(None, urls), _fixtures())[0]
        report = json.loads(layer_info)

        self.assertEqual(tuple(images.shape), (2, BASE_SIZE[1], BASE_SIZE[0], 3))
        self.assertEqual([entry["name"] for entry in report], [f"layer_{idx}" for idx in range(len(urls))])
        for entry in report:
            self.assertIsNone(entry["bounding_box"])
            self.assertEqual(entry["origin"], [0, 0])
            self.assertEqual(entry["size"], list(BASE_SIZE))
        self.assertEqual(float(masks[0].sum()), 0.0)

    def test_out_of_canvas_boxes_are_clipped_instead_of_crashing(self):
        layout = _layout()
        layout[2]["bounding_box"] = {"absolute": [BASE_SIZE[0] - 10, BASE_SIZE[1] - 10, BASE_SIZE[0] + 40, BASE_SIZE[1] + 60]}
        images, masks, _ = self.run_layers(seedream5_pro_layer, _record(layout, ["fixture://base"]), _fixtures())[0]
        self.assertEqual(tuple(images.shape), (3, BASE_SIZE[1], BASE_SIZE[0], 3))
        self.assertEqual(float(masks[2][BASE_SIZE[1] - 1, BASE_SIZE[0] - 1]), 0.0)

    def test_a_layer_without_a_url_is_skipped(self):
        layout = _layout()
        layout[2]["url"] = None
        images, _, layer_info = self.run_layers(seedream5_pro_layer, _record(layout, ["fixture://base"]), _fixtures())[0]
        self.assertEqual(tuple(images.shape), (2, BASE_SIZE[1], BASE_SIZE[0], 3))
        self.assertEqual(len(json.loads(layer_info)), 2)

    def test_malformed_records_raise(self):
        cases = [
            ({}, _fixtures(), "Task completed without resultJson"),
            ({"resultJson": "not json"}, _fixtures(), "not valid JSON"),
            ({"resultJson": json.dumps({"resultUrls": []})}, _fixtures(), "neither layers_data nor resultUrls"),
            (_record([{"z_index": 0, "url": "fixture://broken"}], []),
             {"fixture://broken": b"not an image"}, "Failed to decode result image"),
        ]
        for record, fixtures, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(RuntimeError) as raised:
                    self.run_layers(seedream5_pro_layer, record, fixtures)
                self.assertIn(message, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
