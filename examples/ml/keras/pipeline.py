import json
import numpy as np
import tensorflow as tf
from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()

import inferex


MODEL_PATH = 'minst_keras.h5'


cached_model = None

@inferex.pipeline(name="predict", is_async=False)
def predict(payload: dict) -> dict:

    global cached_model

    try:
        if not cached_model:
            cached_model = tf.keras.models.load_model(MODEL_PATH)

        result = cached_model(payload['digits'])
        return {'result': 'OK', 'payload': result.tolist()}
    except Exception as e:
        return {'result': 'ERROR',
                'payload': str(e)}


if __name__ == '__main__':

    digit = json.loads(open('fixtures/digit_5.json', 'r').read())
    digit['digits'] = np.array(digit['digits'])

    print(predict(digit))
