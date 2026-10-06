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


if __name__ == "__main__":
    unittest.main()
