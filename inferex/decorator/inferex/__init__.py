""" Inferex decorator

Intended usage:

    import inferex

    @inferex.pipeline(name="email-image-inference")
    def func(args):
        return f"Args: {args}"

"""

from .decorators import pipeline

__all__ = ["pipeline"]
