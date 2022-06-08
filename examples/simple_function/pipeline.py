"""
Example runables for testing.
"""

from inferex import pipeline


@pipeline(endpoint="/simple-function")
def simple_function(payload: dict) -> dict:
    """
    Simplest function possible
    """
    return payload
