# Inferex CLI

Inferex CLI - Init, deploy and manage your projects on Inferex infrastructure

[Please see our online documentation](https://docs.inferex.com/)

## 1. Setup

Install the Inferex Python package via pip from PyPI. This provides Command Line Tool (CLI), and decorator code to wrap your Inference code.

    pip install inferex


## 2. Configure your project

Below is an example YOLOv5 pipeline. We're going to modify this code to make it deployable as an API on Inferex.

    import torch

    class YoloPipeline:
        def __init__(self):
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5')

        def infer(img: str) -> dict:
            results = model(img)
            return results

To make our `infer()` function available as an API, we need to `import inferex` to decorate our code.

    import torch
    from inferex import pipeline

    class YoloPipeline:

        def __init__(self):
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5')

        @pipeline(endpoint="/yolo_object_detection")
        def infer(img: str) -> dict:
            results = model(img)
            return results

## 3. Deploy via the CLI

    # Run inferex login to authenticate - Only needs to be done once
    > inferex login

    # Deploy the project folder
    > inferex deploy /path/to/project


