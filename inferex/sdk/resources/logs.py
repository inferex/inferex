""" Class for operations on the Log resource"""
from requests import Response

from inferex.sdk.http import api_session
from inferex.sdk.resources.base_models import LogBase


URL_PATH = "logs"

class Log(LogBase):

    def get(self, start: str = None, end: str = None, limit: int = 1000):
        """ Get logs """
        response = get(git_sha=self.git_sha, start=start, end=end, limit=limit)
        response_data = {'data': response.json(), 'git_sha': self.git_sha}
        logs = Log(**response_data)
        return logs


def get(**kwargs) -> Response:
    """
    Retrive logs for a given deployment.

    Args:
        **kwargs:
            git_sha(str): Git sha of the deployment.
            start(str): ISO formatted datetime string (UTC) lower bound.
            end(str): " upper bound.
            limit(int): Number of rows to return at most.

    Returns:
        response (Response): requests response object.
    """
    response = api_session.request("GET", URL_PATH, params=kwargs)
    return response
