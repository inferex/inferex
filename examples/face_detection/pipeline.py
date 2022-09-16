"""
Example runables for testing.
"""

from facenet_pytorch import MTCNN

import inferex


class FaceDetectionPipeline:
    """
    Example model class for with facenet_pytorch.
    """

    def __init__(self, config: dict = None):
        self.config = config
        self.model = MTCNN(
            image_size=160, margin=0, min_face_size=20, post_process=True
        )

    @inferex.pipeline(
        name="face-detection",
        is_async=False,
    )
    def infer(self, payload: dict) -> dict:
        """
        Performs inference on the payload.
        """
        # TODO: THIS IS BROKEN

        # run inference
        boxes, probs, points = self.model.detect(payload, landmarks=True)
        if None in (boxes, probs, points):
            return {}

        response = {
            "boxes": boxes.tolist(),
            "points": points.tolist(),
            "probs": probs.tolist(),
        }

        return response
