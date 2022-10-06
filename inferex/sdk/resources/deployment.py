""" Contains Deployment related functions. """
from typing import Optional, List
from pathlib import Path
import tempfile
import time

from requests import Response

from inferex.sdk.resources.base_models import DeploymentBase, PipelineBase
from inferex.sdk.resources import project
from inferex.sdk.resources import pipeline
from inferex.utils.io.logs import get_logger
from inferex.utils.io.utils import get_project_config, validate_pipelines
from inferex.utils.io.git import git_sha
from inferex.utils.io.compression import make_archive
from inferex.sdk.http import api_session, create_multipart_encoder_monitor
from inferex.sdk.exceptions import DeployFailureError
from inferex.utils.io.scanning import validate_requirements_txt, RequirementsValidationException


logger = get_logger(__name__)
URL_PATH = "deployments"

class Deployment(DeploymentBase):
    """
    Implements deployment related functions.
    """
    def deploy(self) -> DeploymentBase:
        """ Deploy the object to the server. """
        try:
            response = deploy(**self.dict())
        except RequirementsValidationException as exc:
            logger.warning(f"{exc}")
        except DeployFailureError as exc:
            logger.error(f"Error validating pipeline source code - {exc}")
            raise

        deployed_deployment = Deployment(**response.json())
        return deployed_deployment

    def get(self) -> List[DeploymentBase]:
        """
        GET information about a deployment.

        Returns:
            deployment: A deployment instance.
        """
        response = get(self.git_sha)
        deployments = [Deployment(**obj) for obj in response.json()]
        return deployments

    def delete(self) -> DeploymentBase:
        """
        DELETE a deployment.

        Returns:
            deployment: A Deployment instance.
        """
        response = delete(self.deployment_id)
        # TODO: have the delete return an array of length one and change this line.
        deleted_deployment = Deployment(**response.json())
        return deleted_deployment

    def update(self) -> DeploymentBase:
        """
        PATCH a deployment.

        Returns:
            deployments: A Deployment instance
        """
        raise NotImplementedError

    def pipelines(self) -> List[PipelineBase]:
        """ List pipelines of a project. """
        return pipeline.list(self.git_sha)


def delete(deployment_sha: str = None) -> Response:
    """
    DELETE a deployment.

    Args:
        deployment_sha: Git Sha of the deployment.

    Returns:
        deployment: An instance of the deleted deployment.
    """
    params = {'git_sha': deployment_sha}
    response = api_session.request("DELETE", URL_PATH, params=params)
    return response


def deploy(path: str, token: Optional[str] = None, force: bool = False, stream: bool = False) -> Response:
    """
    Deploy a Deployment object to the server.

    Args:
        path (str): Target directory path of the projec to be deployed. Can be a relative path.
        token (Optional[str]): API token to make the request with.
            By default this is read from local storage.
        force (bool): Force the deployment to deploy, even if an identical
            project (hash of project) exists. Appends a random string of
            the form -xxx" to the deployment git sha.
        stream (bool): Stream the logs of the deployment.
    Raises:
        DeployFailureError
    Returns:
        response: requests response object.
    """
    # Ensure Path
    path = Path(path).resolve()
    logger.info(f"Deploying project: {path}")

    # validate pipelines are defined correctly
    try:
        validate_pipelines(path)
    except (ValueError, OSError) as exc:
        raise DeployFailureError(str(exc))

    except Exception as exc:
        logger.error(f"Exception - {exc}")
        raise DeployFailureError(str(exc))

    # validate imports against requirements.txt
    try:
        validate_requirements_txt(path)
    except RequirementsValidationException as exc:
        logger.error(f"Error validating requirements.txt - {exc}")
        # raise DeployFailureError(str(exc))  # TODO: handle edge cases
        raise

    # Validate project directory
    project_config = get_project_config(path)
    project_name = project_config.get("project", {}).get("name")

    # Default project name to the folder name (or "untitled" if "/")
    if not project_name:
        project_name = path.name or "untitled"
        logger.info(f"inferex.yaml file was not found, project name defaulting to: {project_name}")

    # Post project name to the API
    response = project.create(name=project_name, token=token)
    if not response.ok:
        raise DeployFailureError(
            f"Creating project {project_name} failed."
            f"status_code: {response.status_code}"
        )
    validated_project_name = response.json().get('name')

    # Get the SHA of the project / or generate a new one if it doesn't exist
    git_commit_sha = git_sha(path, randomize=force)  # TODO: rename to deployment_sha

    # Create a temporary directory to store the compressed bundle
    with tempfile.NamedTemporaryFile(delete=True, suffix=".tar.xz") as bundle_file:
        # Compress the bundle
        bundle_path = bundle_file.name
        make_archive(bundle_path, path)
        monitor = create_multipart_encoder_monitor(bundle_path, bundle_file)

        # Pass through deployment.token to request headers
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        deploy_params = {
            "project_name": validated_project_name,
            "git_commit_sha": git_commit_sha,
            "stream": stream,
        }

        # Post the bundle to the API
        headers['Content-Type'] = monitor.content_type
        response = api_session.request(
            "POST",
            URL_PATH,
            data=monitor,
            params=deploy_params,
            headers=headers,
        )

        # Stream logs
        if stream:
            return poll_deployment_status(git_commit_sha=git_commit_sha)

        return response


def get(git_sha_: str = None, project_name: str = None) -> Response:
    """
    GET and list all active deployments and their status.
    GET and list deployments with a given project name.

    Args:
        project_name(str): Name of the project to GET deployments of.

    Returns:
        deployments(list): A list of Deployment instances.
    """
    params = {'git_sha': git_sha_, 'project_name': project_name}
    response = api_session.request("GET", URL_PATH, params=params)
    return response


def poll_deployment_status(git_commit_sha: str):
    stage, substage = "", ""
    while True:

        # Request task status and stage
        response = api_session.request(
            "GET",
            f"{URL_PATH}/status",
            params={"task_id": git_commit_sha},
        )
        if not response.ok:
            yield f"HTTP {response.status_code} Error during deployment: {response.json().get('detail')}"
            break

        # Parse response
        response_json = response.json()
        state = response_json.get("state")
        exception = response_json.get("exception")
        response_stage = response_json.get("stage")
        response_substage = response_json.get("substage")

        # Log stage and substage
        if response_stage and stage != response_stage:
            stage = response_stage
            yield f"→ {stage}"
        if response_substage and substage != response_substage:
            substage = response_substage
            yield f"   ↳ {substage}"
        if exception:
            yield exception
        if state in ("Failed", "SUCCESS"):
            break

        # Sleep for a second
        time.sleep(1)
