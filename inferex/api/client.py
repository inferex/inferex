""" Client to call the API endpoints on Operator, a simple wrapper to requests """

import os
from typing import Callable, Optional
from pathlib import Path

import requests
from requests import Response
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from typer import Exit
from inferex.io.token import cached_token
from inferex.io.termformat import error
from inferex.io.utils import get_project_name, handle_api_response


class OperatorClient:
    """
    A client library to use the HTTP endpoints on Operator

    INFEREX_API_ROOT environment varible is loaded and is used as the API URL ROOT
    its default value is 'http://localhost:8000' for development use
    """

    def __init__(self) -> None:

        self.api_root = os.environ.get("INFEREX_API_ROOT", "https://api.inferex.net")
        self.cached_token = cached_token()

    def _headers(self):
        if not self.cached_token:
            error("No token found. Please run `inferex login`")
            raise Exit(1)

        # Get authorization header
        access_token = self.cached_token.get("access_token")
        authorization = f"Bearer {access_token}"

        # Construct headers
        headers = {
            "Authorization": authorization
        }
        return headers

    def login(self, username: str, password: str) -> Response:
        """Call the /auth/login endpoint on Operator

        Authentication is username/password and the server will return an OAuth2
        compatible jwt bearer token

        Returns:
            api_response (requests.Response): The response from operator /auth/login
        """
        payload = {
            "username": username,
            "password": password,
        }

        api_resonse = requests.post(f"{self.api_root}/auth/login", payload)
        return api_resonse

    def deploy(
        self,
        git_sha: str,
        archive_fullpath: str,
        project_path: Path,
        callback: Callable,
    ) -> Response:
        """Call the /deploy endpoint on operator

        Args:
            git_sha (str): the git sha hash
            archive_fullpath (str): full path to temporary compressed file
            project_path: (Path): path to project folder
            callback (Callable): callback function for progress bar

        Returns:
             (requests.Response): Response from operator /projects/deploy

        Raises:
            Exit: Typer exit on critical error
        """

        with open(archive_fullpath, "rb") as file_pointer:

            encoder = MultipartEncoder(
                fields={"file": (archive_fullpath, file_pointer, "application/x-xz")}
            )

            monitor = MultipartEncoderMonitor(encoder, callback)

            project_name = get_project_name(project_path.resolve())
            create_params = {"project_name": project_name}

            resp = requests.post(
                f"{self.api_root}/projects",
                params=create_params,
                headers=self._headers(),
            )

            if not resp.ok:
                error(f"Non-200 response ({resp.status_code})")
                raise Exit()

            # request to projects/deploy
            deploy_params = {"project_name": project_name, "git_commit_sha": git_sha}

            headers = self._headers()
            headers.update({"Content-Type": monitor.content_type})

            return requests.post(
                f"{self.api_root}/deployments",
                data=monitor,
                params=deploy_params,
                headers=headers,
            )

    def get(self, endpoint: Optional[str] = "/", **kwargs: dict) -> Response:
        """
        Make a GET request to the API endpoint with configured credentials.

        Args:
            endpoint: the endpoint to make a GET request to
            **kwargs: additional arguments to pass to requests.get

        Returns:
            response.json(): a python dictionary if response headers indicate json data
            was returned. Otherwise, exit with code 1.
        """

        # Get headers
        route = self.api_root + endpoint
        headers = self._headers()

        # Make request
        response = requests.get(route, headers=headers, **kwargs)

        # Handle response
        response = handle_api_response(response)

        return response


    def delete(self, endpoint: Optional[str] = "/", **kwargs: dict) -> Response:
        """
        Make a DELETE request to the API endpoint with configured credentials.

        Args:
            endpoint: the endpoint to make a DELETE request to
            **kwargs: additional arguments to pass to requests.post

        Returns:
            response.json(): a python dictionary if response headers indicate json data
            was returned. Otherwise, exit with code 1.
        """

        # Get headers
        route = self.api_root + endpoint
        headers = self._headers()

        # Make request
        response = requests.delete(route, headers=headers, **kwargs)

        # Handle response
        response = handle_api_response(response)

        return response
