""" Contains project related functions."""
from typing import Optional, List

from requests import Response
from inferex.sdk.resources import deployments
from inferex.sdk.resources.base_models import DeploymentBase, ProjectBase
from inferex.sdk.http import api_session


URL_PATH = "projects"

class Project(ProjectBase):
    """
    Implements project related functions.
    """

    def create(self) -> ProjectBase:
        """ Create a project.

        Returns:
            A project instance.
        """
        response = create(name=self.name)
        # TODO: Change create endpoint to return an array with one element.
        #       Then change the line below
        project = Project(**response.json())
        return project

    def get(self) -> List[ProjectBase]:
        """ Get a project.

        Returns:
            A list of Project instances.
        """
        raise NotImplementedError

    def delete(self):
        """ Delete a project. """
        response = delete(self.name)
        deleted_project = Project(**response.json())
        return deleted_project

    def deployments(self) -> List[DeploymentBase]:
        """ List deployments of a project. """
        return deployments.get(project_name=self.name)


def create(name: str, token: Optional[str] = None) -> Response:
    """ Create a new project.

    Args:
        name(str): Project name
        token(str): Optional. API token to authenticate with.

    Returns:
        response (Response): requests response object.
    """
    params = {"project_name": name}
    headers = {"Authorization": f"Bearer {token}"} if token else None
    response = api_session.request(
        "POST",
        URL_PATH,
        params=params,
        headers=headers,
    )
    return response


def list(name: Optional[str] = None) -> Response:  #  pylint: disable=W0622
    """
    Retrieve a project or a list of all projects.

    Args:
        name(str): The name of the project.

    Returns:
        response (Response): requests response object.
    """
    params = {'project_name': name}
    response = api_session.request("GET", URL_PATH, params=params)
    return response


def delete(name: str) -> Response:
    """
    Delete a project.

    Args:
        name (str): the name of the project
    Returns:
        response (Response): requests response object
    """
    params = {'project_name': name}
    response = api_session.request("DELETE", URL_PATH, params=params)
    return response
