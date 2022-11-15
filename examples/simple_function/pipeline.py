import inferex


@inferex.pipeline(name="simple-function")
def simple_function(payload: dict) -> dict:
    return payload
