class SteveHelloNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"name": ("STRING", {"default": "Steve"})}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "steve/examples"

    def run(self, name):
        return (f"hello {name}",)

NODE_CLASS_MAPPINGS = {"SteveHelloNode": SteveHelloNode}
NODE_DISPLAY_NAME_MAPPINGS = {"SteveHelloNode": "Steve: Hello"}
