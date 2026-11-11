"""Run in the Windows ComfyUI Python environment; paid services are mocked."""

from io import BytesIO
import unittest
from unittest.mock import patch

import torch
from PIL import Image

from kie_api import gpt_image2
from kie_api.images import _image_bytes_to_tensor_and_mask


class GPTImageRuntimeTests(unittest.TestCase):
    def test_alpha_is_inverse_mask_and_rgb_is_preserved(self):
        img = Image.new("RGBA", (3, 1))
        img.putdata([(255, 0, 0, 0), (0, 255, 0, 128), (0, 0, 255, 255)])
        data = BytesIO()
        img.save(data, format="PNG")
        image, mask = _image_bytes_to_tensor_and_mask(data.getvalue())
        self.assertEqual(tuple(image.shape), (1, 1, 3, 3))
        self.assertEqual(tuple(mask.shape), (1, 1, 3))
        self.assertEqual(image.dtype, torch.float32)
        torch.testing.assert_close(image[0, 0], torch.eye(3))
        torch.testing.assert_close(mask, torch.tensor([[[1.0, 1.0 - 128 / 255, 0.0]]]))

    def test_opaque_image_yields_full_size_zero_mask(self):
        data = BytesIO()
        Image.new("RGB", (3, 2), "white").save(data, format="PNG")
        _, mask = _image_bytes_to_tensor_and_mask(data.getvalue())
        torch.testing.assert_close(mask, torch.zeros((1, 2, 3)))

    def test_invalid_i2i_fails_before_auth_or_upload(self):
        with patch.object(gpt_image2, "_load_api_key") as auth:
            for overrides in (dict(aspect_ratio="27:16", resolution="4K"),
                              dict(images=torch.zeros((17, 1, 1, 3)))):
                args = dict(prompt="Edit", images=torch.zeros((1, 1, 1, 3)),
                            model="GPT Image 2.5 Flare", aspect_ratio="auto", resolution="1K")
                args.update(overrides)
                with self.assertRaises(RuntimeError):
                    gpt_image2.run_gpt_image2_image_to_image(**args)
            auth.assert_not_called()

    def test_i2i_uploads_references_into_selected_model_payload(self):
        with patch.object(gpt_image2, "_load_api_key", return_value="test"), \
             patch.object(gpt_image2, "_image_tensor_to_png_bytes", return_value=b"png"), \
             patch.object(gpt_image2, "_upload_image", side_effect=["https://a", "https://b"]), \
             patch.object(gpt_image2, "_run_gpt_image2_payload", return_value=("image", "mask")) as run:
            result = gpt_image2.run_gpt_image2_image_to_image(
                prompt="Edit", images=torch.zeros((2, 1, 1, 3)),
                model="GPT Image 2.5 Sunburst", aspect_ratio="auto", resolution="4K", log=False,
            )
            self.assertEqual(result, ("image", "mask"))
            payload = run.call_args.kwargs["payload"]
            self.assertEqual(payload["model"], "gpt-image-2-5-sunburst-image-to-image")
            self.assertEqual(payload["input"]["input_urls"], ["https://a", "https://b"])


class GPTImage26MediaTests(unittest.TestCase):
    def guide(self, **kwargs):
        from kie_api.gpt_image_media import prepare_edit_guide
        args = dict(images=torch.zeros((1, 2, 3, 3)), model="GPT Image 2.6 Flare", output_format="png")
        args.update(kwargs)
        return prepare_edit_guide(**args)

    def test_mask_png_alpha_is_inverse_of_edit_mask(self):
        mask = torch.tensor([[[0., 1., 0.5], [1., 0., 1.]]])
        field, data = self.guide(mask=mask)
        self.assertEqual(field, "mask_url")
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(list(image.getchannel("A").getdata()), [255, 0, 128, 0, 255, 0])

    def test_markup_preserves_color_and_transparency(self):
        annotation = torch.zeros((1, 2, 3, 3))
        annotation[..., 0] = 1
        mask = torch.tensor([[[1., 0., 1.], [1., 1., 1.]]])
        field, data = self.guide(markup=annotation, markup_mask=mask)
        self.assertEqual(field, "markup")
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.getpixel((1, 0)), (255, 0, 0, 255))
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 0))

    def test_bad_guides_fail_before_upload(self):
        bad_cases = [dict(mask=torch.zeros((2, 2, 3))), dict(mask=torch.zeros((1, 3, 2))),
                     dict(mask=torch.full((1, 2, 3), float("nan"))),
                     dict(mask=torch.ones((1, 2, 3)), markup=torch.zeros((1, 2, 3, 3))),
                     dict(markup=torch.zeros((1, 2, 3, 3))),
                     dict(markup=torch.zeros((1, 2, 3, 3)), markup_mask=torch.zeros((1, 2, 3))),
                     dict(mask=torch.zeros((1, 2, 3)), output_format="gif"),
                     dict(mask=torch.zeros((1, 2, 3)), output_format="svg"),
                     dict(mask=torch.zeros((1, 2, 3)), model="GPT Image 2.6 Economy")]
        with patch.object(gpt_image2, "_load_api_key") as auth:
            for overrides in bad_cases:
                args = dict(prompt="Change selected item", images=torch.zeros((1, 2, 3, 3)),
                            model="GPT Image 2.6 Flare", aspect_ratio="auto", resolution="1K")
                args.update(overrides)
                with self.subTest(keys=overrides.keys()), self.assertRaises(RuntimeError):
                    gpt_image2.run_gpt_image2_image_to_image(**args)
            auth.assert_not_called()

    def test_guide_upload_is_separate_from_reference_urls(self):
        with patch.object(gpt_image2, "_load_api_key", return_value="test"), \
             patch.object(gpt_image2, "_upload_image", side_effect=["https://source", "https://mask"]), \
             patch.object(gpt_image2, "_run_gpt_image2_payload", return_value=()) as run:
            gpt_image2.run_gpt_image2_image_to_image(
                prompt="Edit", images=torch.zeros((1, 2, 3, 3)), mask=torch.ones((1, 2, 3)),
                model="GPT Image 2.6 Sunburst", aspect_ratio="auto", resolution="1K", log=False)
            inputs = run.call_args.kwargs["payload"]["input"]
            self.assertEqual(inputs["input_urls"], ["https://source"])
            self.assertEqual(inputs["mask_url"], "https://mask")

    def test_gif_frames_timing_and_original_bytes_survive(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from kie_api.gpt_image_media import collect_results
        data = BytesIO()
        Image.new("RGB", (3, 2), "red").save(data, format="GIF", save_all=True,
            append_images=[Image.new("RGB", (3, 2), "blue")], duration=[100, 230], loop=0)
        with TemporaryDirectory() as directory:
            image, mask, paths, svg, metadata = collect_results(
                [("https://result", data.getvalue())], task_id="test", output_format="gif", output_dir=directory)
            self.assertEqual(tuple(image.shape), (2, 2, 3, 3))
            self.assertEqual(tuple(mask.shape), (2, 2, 3))
            self.assertEqual(Path(json.loads(paths)[0]).read_bytes(), data.getvalue())
            record = json.loads(metadata)["outputs"][0]
            self.assertEqual(record["frame_durations_ms"], [100, 230])
            self.assertEqual(record["loop"], 0)
            self.assertEqual(svg, "")

    def test_svg_is_native_text_and_file_without_fake_image(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from kie_api.gpt_image_media import collect_results, decode_result
        data = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><path d="M0 0L10 10"/></svg>'
        with TemporaryDirectory() as directory:
            image, mask, paths, svg, metadata = collect_results(
                [("https://result", data)], task_id="test", output_format="svg", output_dir=directory)
            self.assertIsNone(image)
            self.assertIsNone(mask)
            self.assertEqual(svg, data.decode())
            self.assertEqual(Path(json.loads(paths)[0]).read_bytes(), data)
        with self.assertRaises(RuntimeError):
            decode_result(b'<html>error</html>', "svg")
        with self.assertRaises(RuntimeError):
            decode_result(data, "png")

    def test_all_raster_result_urls_are_retained(self):
        import json
        from tempfile import TemporaryDirectory
        from kie_api.gpt_image_media import collect_results
        data = BytesIO()
        Image.new("RGB", (3, 2), "red").save(data, format="PNG")
        with TemporaryDirectory() as directory:
            result = collect_results([("https://a", data.getvalue()), ("https://b", data.getvalue())],
                task_id="test", output_format="png", output_dir=directory)
            self.assertEqual(result[0].shape[0], 2)
            self.assertEqual(len(json.loads(result[2])), 2)


if __name__ == "__main__":
    unittest.main()
