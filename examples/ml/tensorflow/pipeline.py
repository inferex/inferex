import json
import numpy as np
import os
import tensorflow as tf

from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()

import inferex


WEIGHTS_PATH = "./tf_weights/weights"


def create_model():

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10)
    ])

    return model


def load_model():
    model = create_model()
    if os.path.exists(WEIGHTS_PATH):
        model.load_weights(WEIGHTS_PATH)
    return model


cached_model = None

@inferex.pipeline(name="predict", is_async=False)
def predict(payload: dict) -> dict:

    global cached_model

    try:
        if not cached_model:
            cached_model = load_model()

        result = cached_model(payload['digits'])
        return {'result': 'OK', 'payload': result.tolist()}
    except Exception as e:
        return {'result': 'ERROR',
                'payload': str(e)}


if __name__ == '__main__':
    digit = json.loads(open('fixtures/digit_5.json', 'r').read())
    digit['digits'] = np.array(digit['digits'])

    print(predict(digit))
