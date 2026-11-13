"""Native V3 GPT Image nodes. Legacy IDs remain registered separately."""

from comfy_api.latest import io

from .kie_api.gpt_image_dynamic import model_input, request_options


def _schema(node_id, display_name, mode):
    inputs = [io.String.Input("prompt", multiline=True)]
    if mode == "image-to-image":
        inputs.append(io.Image.Input("images"))
    inputs += [model_input(io, mode), io.Boolean.Input("log", default=True)]
    return io.Schema(
        node_id=node_id, display_name=display_name, category="kie/api", inputs=inputs,
        outputs=[io.Image.Output("image"), io.Mask.Output("mask"),
                 io.String.Output("file_paths"), io.String.Output("svg"), io.String.Output("metadata")],
        description="Select model and Image/SVG/GIF mode. Only relevant native inputs are shown. "
                    "SVG returns file/text outputs, not IMAGE/MASK. Originals are saved under output/kie_gpt_image.",
    )


class KIE_GPTImage_TextToImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return _schema("KIE_GPTImage_TextToImage", "KIE GPT Image (Text-to-Image)", "text-to-image")

    @classmethod
    def execute(cls, prompt, model, log=True):
        from .kie_api.gpt_image2 import run_gpt_image2_text_to_image
        args = request_options(prompt, model, "text-to-image")
        return io.NodeOutput(*run_gpt_image2_text_to_image(prompt=prompt, log=log, **args))


class KIE_GPTImage_ImageToImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return _schema("KIE_GPTImage_ImageToImage", "KIE GPT Image (Image-to-Image)", "image-to-image")

    @classmethod
    def execute(cls, prompt, images, model, log=True):
        from .kie_api.gpt_image2 import run_gpt_image2_image_to_image
        args = request_options(prompt, model, "image-to-image")
        return io.NodeOutput(*run_gpt_image2_image_to_image(prompt=prompt, images=images, log=log, **args))
