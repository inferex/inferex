import transformers

import inferex


class TextGenerationPipeline:
    """
    Example model class for with Python transformers.
    """

    def __init__(self):
        # load model
        self.model = transformers.pipeline(task="text-generation")

    @inferex.pipeline(name="text-generation")
    def infer(self, payload: dict) -> dict:
        """
        Performs inference on the payload.
        """
        # run inference
        response = self.model(payload["text"])[0]
        return response
