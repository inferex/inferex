""" Client to call the API endpoints on Operator, a simple wrapper to requests """

import os
import sys
import json
import tarfile
import tempfile
import urllib.parse
from pathlib import Path
from contextlib import suppress
from typing import Optional, Union

import click
import yaspin
import requests
from tqdm import tqdm
from requests import Response
from humanize import naturalsize
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from inferex import __app_name__
from inferex.io.git import git_sha
from inferex.io.termformat import SPINNER_COLOR, info, success, error
from inferex.io.utils import get_project_config


class Client:
    """
    A client library to use the HTTP endpoints on Operator

    INFEREX_API environment varible is loaded and is used as the API URL ROOT
    its default value is 'http://localhost:8000' for development use
    """

    IGNORED_PATTERNS = [
        "venv",
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".egg-info",
        ".vscode",
        "/dist",
    ]
    DEFAULT_PROJECT_CONFIG = "project:\n  name: {}\n"

    # Set API for production or development
    INFEREX_DEV = os.getenv("INFEREX_DEV") == "true"
    if INFEREX_DEV:
        DEFAULT_API = "http://localhost:8000"
    else:
        DEFAULT_API = "https://api.inferex.net"

    def __init__(self) -> None:

        self.token_path = Path(
            click.get_app_dir(__app_name__, force_posix=True)
        ) / "token.json"
        self.api_root = os.getenv("INFEREX_API", self.DEFAULT_API)

    def init(self, project_path: str):
        """Creates a new project in the target folder."""
        project_path = Path(project_path)

        # Check if inferex.yaml already exists
        yaml_file = project_path / "inferex.yaml"
        if yaml_file.is_file():
            info(f"{yaml_file} already exists.")
            sys.exit(0)

        # Create inferex.yaml
        project_name = click.prompt("Project name")
        with open(yaml_file, "w", encoding="UTF-8") as file:
            file.write(self.DEFAULT_PROJECT_CONFIG.format(project_name))

        success(f"Project initialized at {click.format_filename(project_path.absolute())}.")
        info("📝 Edit the 'inferex.yaml' file to customize deployment parameters.\n")

    def login(self, username: str, password: str) -> Response:
        """Call the /auth/login endpoint on Operator

        Authentication is username/password and the server will return an OAuth2
        compatible jwt bearer token

        Returns:
            api_response (requests.Response): The response from operator /login
        """

        # Call the login endpoint
        response = self.post(
            "login",
            data={
                "username": username,
                "password": password,
            },
            headers={"Authorization": ""},
        )

        # Store the token in the cache
        if response.ok:
            # Convert to json
            response = response.json()

            # Store the token
            self._set_token(response)
            success("Login OK\n")

        return response

    def reset(self) -> None:
        """Reset the token and cache"""
        if self.token_path.is_file():
            self.token_path.unlink()
            info(f"Deleted {click.format_filename(self.token_path)}")
        if self.token_path.parent.name == ".inferex":
            self.token_path.parent.rmdir()
            info(f"Deleted {click.format_filename(self.token_path.parent)}")

    def deploy(
            self,
            project_path: Union[Path, str],
            force: bool=False,
            token: Optional[str] = None
    ) -> Response:
        """Deploy the project to Operator.

        Args:
            project_path (Union[Path, str]): The path to the users Inferex project folder

            force (bool): Uses a random SHA as the deployment ID to circumvent duplicate
                          deploy detection
            token (str, None): JWT token issued to user.
        """

        # Ensure Path
        info(f"Deploying: {project_path}")
        project_path = Path(project_path).resolve()

        # Validate project directory
        project_config = get_project_config(project_path)
        project_name = project_config.get("project", {}).get("name")

        # Default project name to the folder name (or "untitled" if "/")
        if not project_name:
            project_name = project_path.name or "untitled"
            info(f"inferex.yaml file was not found, project name defaulting to: {project_name}")

        # If token was passed, populate headers
        if token:
            headers = {"Authorization": "Bearer " + token}
        else:
            headers = {}

        # Post project name to the API
        response = self.post(
            "projects",
            params={"project_name": project_name},
            headers=self._headers(headers),
        )

        # Get the SHA of the project / or generate a new one if it doesn't exist
        git_commit_sha = git_sha(project_path, randomize=force)  # TODO: rename to deployment_sha

        # Create a temporary directory to store the compressed bundle
        with tempfile.NamedTemporaryFile(delete=True, suffix=".tar.xz") as bundle_file:

            # Compress the bundle
            bundle_path = bundle_file.name
            bundle_size = self._compress(bundle_path, project_path)

            # Create a multipart/form-data request
            encoder = MultipartEncoder(
                fields={"file": (bundle_path, bundle_file, "application/x-xz")}
            )
            monitor = MultipartEncoderMonitor(encoder, callback=None)
            monitor.bundle_size = bundle_size

            # Get deployment params
            deploy_params = {
                "project_name": project_name,
                "git_commit_sha": git_commit_sha,
            }
            headers.update({"Content-Type": monitor.content_type})

            # Post the bundle to the API
            response = self.post(
                "deployments",
                data=monitor,
                params=deploy_params,
                headers=headers,
            )

            if response.ok:
                success("Deploy complete")
            else:
                error(f"Status code ({response.status_code}) not ok.")

    def _compress(self, tar_path: Path, target_dir: Path):
        """Compress a bundle of the users project into a tar.xz archive

        Args:
            tar_path (Path): The path to the tar.xz archive
            target_dir (Path): The path to the users Inferex project folder,
        """

        # Progress spinner
        progress = self._progress(text="Compressing")

        try:
            # Track the size of the bundle
            bundle_size = 0

            # Create a tar.xz archive # TODO: detect if LZMA is supported
            # See: https://github.com/python/cpython/blob/main/Lib/tarfile.py#L1744
            tar = tarfile.open(tar_path, "w:xz")  # pylint: disable=consider-using-with
            for file_path in Path(target_dir).glob('**/*'):

                # Ignore bad files or directories
                file_path_str = str(file_path)
                if any(pattern in file_path_str for pattern in self.IGNORED_PATTERNS):
                    # TODO: if very verbose, list files that are added / ignored
                    continue

                # Get size and relative path
                bundle_size += file_path.stat().st_size
                relative_path = file_path.relative_to(target_dir)

                # Add the file to the tar archive
                tar.add(file_path, arcname=relative_path)
        except (ValueError, tarfile.CompressionError, tarfile.ReadError) as exc:
            self._handle_exception(exc)
        finally:
            tar.close()
            progress.close()

        success(f"Bundle prepared: {naturalsize(bundle_size)}, {bundle_size}")
        return bundle_size

    def _progress(
        self,
        monitor: Union[MultipartEncoderMonitor, None] = None,
        text: str = "",
    ) -> Union[tqdm, yaspin.Spinner]:
        """Display a progress spinner while the request is in progress.

        Args:
            monitor (Union[MultipartEncoderMonitor, None], optional): A monitor object
            text (str, optional): The text to display on loading.

        Returns:
            _type_: _description_
        """
        # If being piped, return a no-op object with a .close() method
        if not sys.stdout.isatty():
            return type("", (object,), {'close': lambda _: None})()

        # Progress bar/spiral
        if isinstance(monitor, MultipartEncoderMonitor):
            progress = tqdm(
                total=monitor.bundle_size,
                unit="B",
                unit_scale=True,
                desc=text or "Uploading",
                ncols=80,
                leave=False,
            )
            monitor.callback = lambda monitor: progress.update(monitor.bytes_read - progress.n)
        else:
            progress = yaspin.yaspin(text=text or "Waiting for response", color=SPINNER_COLOR)
            progress.close = progress.stop
            progress.start()
        return progress

    def _set_token(self, token: dict) -> None:
        try:
            # Make sure the token is a dictionary
            if not token.get("access_token"):
                raise ValueError(f"Token format is not valid: {token}")

            # Ensure directory exists
            self.token_path.parent.mkdir(parents=True, exist_ok=True)

            # Write token to file
            with open(self.token_path, "w", encoding="utf-8") as file:
                json.dump(token, file)
        except (
            ValueError, FileNotFoundError, PermissionError, json.JSONDecodeError
        ) as exc:
            error(f"Failed to set token: \n{str(exc)}")

    @property
    def token(self) -> bool:
        """Get the users OAuth token from the filesystem cache."""
        try:
            token = os.getenv("INFEREX_TOKEN")
            if token:
                return token

            if not self.token_path.is_file():
                raise FileNotFoundError

            # Read token from file
            with open(self.token_path, "r", encoding="utf-8") as file:
                token = json.load(file).get("access_token")
                return token
        except (FileNotFoundError, json.JSONDecodeError):
            error(f"No token present in {self.token_path}, exiting.")
            info("Did you get a token with 'inferex login'?")
            sys.exit(1)

    def _headers(self, headers: Optional[dict] = None) -> dict:
        headers = headers or {}

        if "Authorization" not in headers:
            # Update headers with authorization token
            headers.update({"Authorization": f"Bearer {self.token}"})
        return headers

    def _response_hook(self, response: Response) -> None:
        # Healthy responses don't need to be handled
        if response.ok:
            return

        # Handle forbidden responses
        if response.status_code == requests.codes.forbidden:
            error(f"Forbidden ({response.status_code}), please try again.")

        # Get response detail
        detail = response.text
        with suppress(requests.exceptions.JSONDecodeError, AttributeError):
            detail = response.json().get("detail")

        # Log response status & detail
        error(f"{response.status_code} response from server.")
        info(f"Response Detail: {detail}")
        sys.exit(1)

    def _handle_exception(self, exception: Exception) -> None:
        """Handle an exception that occurred during a request.

        Args:
            exception (Exception): The exception that occurred.
        """
        error(str(exception))
        info(
            "\nYou can set the INFEREX_API environment "
            "varible to point to a different server, "
            f"current config is: {self.api_root}\n"
        )
        sys.exit(1)

    def _request(self, method: str, path: str, **kwargs: dict) -> Response:
        """Make a request to the Operator API

        Args:
            method (str): The HTTP method to use.
            path (str): The path to the endpoint.

        Returns:
            Response: The response from the API.
        """

        # Get parameters
        url = urllib.parse.urljoin(self.api_root, path)
        headers = self._headers(kwargs.pop("headers", None))

        # Start progress bar
        progress = self._progress(kwargs.get("data"))

        try:
            # Make request to API
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                **kwargs
            )
        except requests.exceptions.RequestException as exc:
            self._handle_exception(exc)
        finally:
            progress.close()

        # Run response hook
        self._response_hook(response)

        return response

    def __getattribute__(self, __name: str) -> Response:
        # Allow client.<http_method> to use the _request method
        if __name not in dir(requests.api):
            return super().__getattribute__(__name)
        def wrapper(*args, **kwargs):
            return self._request(__name, *args, **kwargs)
        return wrapper
