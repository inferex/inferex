"""
Example runables for testing.
"""
import transformers

import inferex


class TextClassificationPipeline:
    """
    Example model class for with Python transformers.
    """

    def __init__(self):
        # load model
        self.model = transformers.pipeline(task="text-classification")

    @inferex.pipeline(name="text-classification")
    def infer(self, payload: dict) -> dict:
        """
        Performs inference on the payload.
        """
        # run inference
        response = self.model(payload["text"])[0]
        return response
