"""
Decorator used to wrap inference functions in the users pipeline.
"""
from functools import wraps
from typing import Callable


def pipeline(
    name: str=None, is_async: bool=False, timeout: int=None
) -> Callable:
    """ Wrapper for inference functions in the users pipeline.

    Args:
        name (str): The name of this pipeline.
        is_async (bool): Whether to use async inference.
        timeout (int): The timeout for inference.

    Returns:
        decorator (Callable): The wrapped inference function.
    """

    def decorator(func: Callable):
        """Decorator for said function.

        Args:
            func: The users function to decorate

        Returns:
            wrapper: The decorated function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):

            # - call locally (in process)
            response = func(*args, **kwargs)

            return response

        wrapper.is_decorated_ = True  # Necessary for pipeline discovery
        wrapper.name_ = name
        wrapper.is_async_ = is_async
        wrapper.timeout_ = timeout
        return wrapper

    return decorator
