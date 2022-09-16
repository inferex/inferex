
import torch
import inferex
import requests
from PIL import Image
from io import BytesIO


class YoloPipeline:

    def __init__(self):
        self.model = torch.hub.load(
            'ultralytics/yolov5',
            'yolov5s',
            device='cpu'
        )

    @inferex.pipeline(name="yolo_object_detection")
    def infer(self, request: dict) -> dict:
        # Download the image
        response = requests.get(request.get("url"))
        img = Image.open(BytesIO(response.content))

        # Run inference
        results = self.model(img)

        # Format
        results = results.pandas().xyxy[0].to_dict(orient="records")
        return results
