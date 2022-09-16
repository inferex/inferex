import json
import numpy as np
import os
this_path = os.path.dirname(os.path.realpath(__file__))

from train import LitMNIST


import inferex


CHECKPOINT_PATH = os.path.join(this_path, "lightning_logs", "version_0", "checkpoints", "epoch=0-step=1719.ckpt")


cached_model = None

@inferex.pipeline(name="predict", is_async=False)
def predict(payload: dict) -> dict:

    global cached_model

    try:
        if not cached_model:
            cached_model = LitMNIST.load_from_checkpoint(CHECKPOINT_PATH, strict=False)
            cached_model.eval()

        print(cached_model)
        result = cached_model(payload['digits'])
        return {'result': 'OK', 'payload': result}
    except Exception as e:
        return {'result': 'ERROR',
                'payload': str(e)}


if __name__ == '__main__':
    digit = json.loads(open('fixtures/digit_5.json', 'r').read())
    digit['digits'] = np.array(digit['digits'])

    print(predict(digit))
