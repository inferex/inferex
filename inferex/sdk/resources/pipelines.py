""" Contains pipeline related functions. """
from typing import List

from requests import Response

from inferex.sdk.http import api_session
from inferex.sdk.resources.base_models import PipelineBase


URL_PATH = "pipelines"

class Pipeline(PipelineBase):
    """
    Implements pipeline related functions.
    """

    def delete(self) -> PipelineBase:
        """ Delete an pipeline. """
        raise NotImplementedError

    def list(self) -> List[PipelineBase]:
        """ Retrieve pipelines with a deployment's git sha. """
        response = list(git_sha=self.git_sha)
        pipelines = [Pipeline(**obj) for obj in response.json()]
        return pipelines


def get(name: str) -> Response:
    """
    Retrieve pipeline data by name (To be implemented).

    Args:
        git_sha (str): Git sha of the deployment.

    Returns:
        response (Response): requests response object.
    """
    raise NotImplementedError


def list(git_sha: str) -> Response:  # pylint: disable=W0622
    """
    Retrieve pipelines of a deployment.

    Args:
        git_sha (str): Git sha of the deployment.

    Returns:
        response (Response): requests response object.
    """
    params = {'git_sha': git_sha}
    response = api_session.request("GET", URL_PATH, params=params)
    return response
