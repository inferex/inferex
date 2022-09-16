import joblib
import json
import numpy as np

import inferex


cached_model = None

@inferex.pipeline(name="predict", is_async=False)
def predict(payload: dict) -> dict:

    global cached_model

    try:
        if not cached_model:
            cached_model = joblib.load('clf.joblib')

        result = cached_model.predict(payload['digits'])
        return {'result': 'OK', 'payload': result.tolist()}
    except Exception as e:
        return {'result': 'ERROR',
                'payload': str(e)}


if __name__ == '__main__':

    digit = json.loads(open('fixtures/predict.json', 'r').read())
    payload = {'digits': np.array([digit, ])}

    print(predict(payload))
