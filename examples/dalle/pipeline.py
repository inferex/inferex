"""
Example runables for testing.
"""

import inferex
from min_dalle import MinDalle
import torch
import base64
from io import BytesIO


model = MinDalle(
    models_root='./pretrained',
    dtype=torch.float32,
    device='cpu',
    is_mega=False,
    is_reusable=True
)

@inferex.pipeline(name="generate")
def generate(payload: dict) -> dict:

    image = model.generate_image(
        text=payload['text'],
        seed=-1,
        grid_size=1,
        is_seamless=False,
        temperature=1,
        top_k=256,
        supercondition_factor=32,
        is_verbose=False
    )

    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())

    return {'image': img_str.decode('utf-8')}
