""" Contains Deployment related functions. """
import os
import random
import string
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import List, Optional

import click
from dirhash import dirhash
from requests import Response

from inferex.sdk.exceptions import DeployFailureError
from inferex.sdk.http import api_session, create_multipart_encoder_monitor
from inferex.sdk.logs import get_logger
from inferex.sdk.resources import pipelines, projects
from inferex.sdk.resources.base_models import DeploymentBase, PipelineBase
from inferex.cli.terminal_format import error, info
from inferex.common.project import get_project_config
from inferex.sdk.validation import validate_pipelines


logger = get_logger(__name__)

URL_PATH = "deployments"

IGNORE_FILE_NODES = [
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".egg-info",
    ".vscode",
    "dist",
]

SHORT_SHA_LENGTH = 8

PROJECT_BYTES_WARNING_LIMIT =100_000_000  # 100MB

class Deployment(DeploymentBase):
    """
    Implements deployment related functions.
    """
    def deploy(self) -> DeploymentBase:
        """ Deploy the object to the server. """
        try:
            response = deploy(**self.dict())
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
        return pipelines.list(self.git_sha)


def get(git_sha: str = None, project_name: str = None) -> Response:
    """
    GET and list all active deployments and their status.
    GET and list deployments with a given project name.

    Args:
        project_name(str): Name of the project to GET deployments of.

    Returns:
        deployments(list): A list of Deployment instances.
    """
    params = {'git_sha': git_sha, 'project_name': project_name}
    response = api_session.request("GET", URL_PATH, params=params)
    return response


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


def display_project_size_warning(bundle_size_bytes: int, project_warning_bytes: int):
    """
    Prints a message to the user warning how large their project is.

    Args:
        bundle_size_bytes(int): number of bytes of the bundle
        project_warning_bytes(int): number of bytes the bundle must exceed in
            order to display the warning.
    """
    if bundle_size_bytes > project_warning_bytes:  # 100MB
        click.echo(
            f"Project exceeds {project_warning_bytes / 1000 / 1000} MB. "
            "Maybe you've left your venv or weights in the project. "
            "It is recommended to use a .ixignore file and pull artifacts at build time."
        )


def deploy(path: str, token: Optional[str] = None, force: bool = False, stream: bool = False) -> Response:
    """
    Deploy a Deployment object to the server.

    Args:
        path (str): Target directory path of the project to be deployed. Can be a relative path.
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
    path = Path(path).resolve()
    if not path.exists():
        error(f"{path} does not exist.")
        sys.exit()

    logger.info(f"Deploying project: {path}")

    # validate pipelines are defined correctly
    # if not, halt the deploy before server resources are allocated
    try:
        validate_pipelines(path)
    except (ValueError, OSError) as exc:
        raise DeployFailureError(str(exc))

    except Exception as exc:
        logger.error(f"Exception - {exc}")
        raise DeployFailureError(str(exc))

    # checks if inferex.yaml is valid
    project_config = get_project_config(path)
    project_name = project_config.get("project", {}).get("name")

    if not project_name:
        project_name = path.name or "untitled"
        logger.info(f"inferex.yaml file was not found, project name defaulting to: {project_name}")

    # create and validate project name server side
    response = projects.create(name=project_name, token=token)
    if not response.ok:
        raise DeployFailureError(
            f"Creating project {project_name} failed."
            f"status_code: {response.status_code}"
        )

    validated_project_name = response.json().get('name')

    # gets latest git commit sha, or computes a hash of the directory if git is not used
    git_commit_sha = get_git_sha(path, randomize=force)

    # Create a temporary directory to store the compressed bundle to not leave behind bloat
    with tempfile.NamedTemporaryFile(delete=True, suffix=".tar.xz") as bundle_file:
        bundle_path = bundle_file.name
        bundle_size_bytes = make_archive(bundle_path, path)
        display_project_size_warning(bundle_size_bytes, PROJECT_BYTES_WARNING_LIMIT)
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
            return poll_deployment_status(response.json().get('task_id'))

        return response


def hash_project_directory(target_dir: str) -> str:
    """ Hash the project directory. Skip ignored files as
        defined by `.ixignore` and `IGNORE_FILE_NODES`.
    """
    # skip potentially expensive hashes
    filenames_to_ignore = get_ixignore_filenodes(target_dir)
    deployment_sha = dirhash(
        target_dir,
        "sha1",
        ignore=filenames_to_ignore + IGNORE_FILE_NODES
    )
    return deployment_sha


def get_git_sha(target_dir: Path, randomize=False) -> str:
    """Get the current git project SHA

    If the given path (or anywhere in parent directories) is a git repo, then
    the current git commit SHA is returned

    Args:
        target_dir (Path): A path to the current project
        randomize (Bool): Add entropy to SHA to circumvent duplicate detection

    Returns:
        sha (str): A git SHA of the users repo
    """
    if not any(target_dir.iterdir()):
        error(f"{target_dir} is empty, please add files to it.")
        sys.exit()

    # obtain project hash (aka git_sha) with dirhash
    deployment_sha = hash_project_directory(target_dir)
    deployment_sha = deployment_sha[:SHORT_SHA_LENGTH]

    if randomize:
        rand_string = ''.join(  # nosec
            random.choice(string.ascii_lowercase + string.digits) for _ in range(3)
        )
        deployment_sha = f"{deployment_sha}-{rand_string}"

    info(f"Your deployment SHA is: {deployment_sha}")

    return deployment_sha


def get_ixignore_filenodes(target_dir: Path) -> List[str]:
    """
    Check .ixignore in the target path for files.
    Return a list of filenames.

    Args:
        target_dir(Path): the project folder to check for a .ixignore file.

    Returns:
        ignore_list(list): a list of filenames to ignore.
    """
    ixignore_file = target_dir / ".ixignore"
    ignore_list = ['.ixignore', ]
    if not ixignore_file.exists():
        logger.warning(f"{ixignore_file} does not exist.")
        return ignore_list

    with open(ixignore_file, "r", encoding="utf-8") as f:
        while (line := f.readline().rstrip()):
            ignore_list.append(line)

    return ignore_list


def gather_file_paths(target_dir: Path) -> List[Path]:
    """
    Recurse target directory and create a list of file paths.
    Ignore certain filesystem nodes based on IGNORE_FILE_NODES
    and .ixignore file, if it exists.

    Args:
        target_dir(Path): Target directory to walk.

    Returns:
        file_paths(list): A list of file Path objects.
    """
    file_paths = []
    ixignore_nodes = get_ixignore_filenodes(target_dir)
    ignore_nodes = IGNORE_FILE_NODES + ixignore_nodes
    for root, dirs, files in os.walk(target_dir, topdown=True):
        skipped_dirs = list(set(dirs).intersection(set(ignore_nodes)))

        for skip_dir in skipped_dirs:
            logger.info(f"Ignoring directory: {skip_dir}")

        # filter out ignored directory names
        dirs[:] = [d for d in dirs if d not in ignore_nodes]
        for file in files:
            file_path = Path(root) / file
            file_or_dir_name = file_path.resolve().name
            # log ignored files
            if any(ignore_node in file_or_dir_name for ignore_node in ignore_nodes):
                logger.info(f"Ignoring file: {file_path}")
                continue
            file_paths.append(file_path)

    return file_paths


def make_archive(archive_path: Path, target_dir: Path) -> int:
    """Compress a bundle of the users project into a tar.xz archive

    Args:
        tar_path (Path): The path to the tar.xz archive
        target_dir (Path): The path to the users Inferex project folder,

    Returns:
        bundle_size(int): The size of the archive.
    """
    # Create a tar.xz archive
    # See: https://github.com/python/cpython/blob/main/Lib/tarfile.py#L1744
    # TODO: detect if LZMA is supported
    bundle_size = 0
    try:
        tar = tarfile.open(archive_path, "w:xz")  # pylint: disable=consider-using-with
        file_paths = gather_file_paths(target_dir)
        for file_path in file_paths:
            # Get size and relative path
            bundle_size += file_path.stat().st_size
            relative_path = file_path.relative_to(target_dir)
            # Add the file to the tar archive
            tar.add(file_path, arcname=relative_path)

    except (ValueError, tarfile.CompressionError, tarfile.ReadError) as exc:
        logger.error(f"Error while compressing {target_dir} - {exc}")

    finally:
        tar.close()

    return bundle_size


def poll_deployment_status(task_id: str):
    stage, substage = "", ""
    while True:

        # Request task status and stage
        response = api_session.request(
            "GET",
            f"{URL_PATH}/status",
            params={"task_id": task_id},
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

        time.sleep(1)
