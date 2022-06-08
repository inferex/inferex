"""
Decorator used to wrap inference functions in the users pipeline.
"""
from functools import wraps
from typing import Callable


def pipeline(dataloader=None, endpoint=None, is_async=False, timeout=None) -> Callable:
    """Wrapper for inference functions in the users pipeline.

    Args:
        dataloader (DataLoader): The dataloader to use for inference.
        endpoint (str): The endpoint to use for inference.
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
        def wrapper(*args):

            # Load data from dataloader
            args = list(args)
            if dataloader is not None:
                args[-1] = dataloader(args[-1])  # pragma: no cover

            # - call locally (in process)
            response = func(*args)

            return response

        wrapper.is_decorated_ = True
        wrapper.dataloader_ = dataloader
        wrapper.endpoint_ = endpoint
        wrapper.is_async_ = is_async
        wrapper.timeout_ = timeout
        return wrapper

    return decorator
