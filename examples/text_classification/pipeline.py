"""
Example runables for testing.
"""
import transformers

from inferex import pipeline


class TextClassificationPipeline:
    """
    Example model class for with Python transformers.
    """

    def __init__(self, config: dict):
        self.config = config
        # load model
        self.model = transformers.pipeline(task="text-classification")

    @pipeline(endpoint="/text-classification")
    def infer(self, payload: dict) -> dict:
        """
        Performs inference on the payload.
        """
        # run inference
        response = self.model(payload["text"])[0]
        return response
