"""
Example runables for testing.
"""
import transformers

import inferex


class SentimentAnalysisPipeline:
    """
    Example model class for with Python transformers.
    """

    def __init__(self):
        # load model
        self.model = transformers.pipeline(task="sentiment-analysis")

    @inferex.pipeline(name="sentiment-analysis")
    def infer(self, payload: dict) -> dict:
        """
        Performs inference on the payload.
        """
        # run inference
        response = self.model(payload["text"])[0]
        return response
