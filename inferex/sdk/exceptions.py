""" Custom exception classes. """

from requests.exceptions import RequestException


class InferexApiError(RequestException):
    """ An error occured during a network request. """
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class DeployFailureError(Exception):
    """ A deployment failed to deploy. """
