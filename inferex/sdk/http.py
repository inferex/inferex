""" HTTP related operations (session, headers, url, retries, exception handling). """
import os
import sys
import platform
from urllib.parse import urljoin
from pathlib import Path
from dotenv import load_dotenv
from typing import Union, BinaryIO

import requests
from requests import Response
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm
import yaspin

from inferex import __version__
from inferex.sdk.settings import settings
from inferex.sdk.logs import get_logger
from inferex.cli.terminal_format import SPINNER_COLOR
from inferex.sdk.exceptions import InferexApiError


logger = get_logger(__name__)

retry_strategy = Retry(
    total=3,
    backoff_factor=0.2,
    status_forcelist=[413, 418, 500, 502, 503, 504, 507],
    raise_on_status=False,  # Do not raise an exception, just return the errored response.
)

class ApiClientSession(requests.Session):
    """
    Client for making HTTP requests.
    """

    def __init__(self, base_url, api_token, verify=True):
        super().__init__()
        self.base_url = base_url
        self.verify = verify
        self.headers['Accept'] = "application/json"
        self.headers['Authorization'] = f"Bearer {api_token}"
        self.headers['User-Agent'] = f"inferex v{__version__} {platform.system()}"
        self.hooks['response'] = [self.log_response, self.handle_errors]
        self.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        self.mount('https://', HTTPAdapter(max_retries=retry_strategy))

    def request(self, method, url_path, params=None, data=None, headers=None) -> Response:
        """ Send a request to the configured server. """
        request_url = urljoin(self.base_url, url_path)
        headers = {**self.headers, **headers} if headers else self.headers
        # don't spin on status checks
        if "status" not in url_path:
            progress_bar = start_progress_bar(data)
        else:
            progress_bar = create_patched_progress_bar()

        try:
            response = super().request(
            method,
            request_url,
            params=params,
            data=data,
            headers=headers
        )
        except Exception as exc:
            logger.error(exc)
            if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
                status_code = f"{exc.response.status_code} "
            else:
                status_code = ""
            if (
                hasattr(exc, "response") and
                "application/json" in exc.response.headers.get("Content-Type", {})
                ):
                detail = "\n" + exc.response.json().get("detail", "")
            else:
                detail = " "
            msg = (
                f"{status_code}{exc.__class__.__name__} "
                f"on {method} to {self.base_url}/{url_path}{detail}"
            )
            raise InferexApiError(msg=msg) from exc
        finally:
            progress_bar.close()

        return response

    def log_response(self, resp: Response, **kwargs) -> None:  # pylint: disable=W0613,R0201
        """
        Write a log message with the response's JSON message. Log level depends
        on the response's status code.
        """
        level = 20 if resp.status_code < 400 else 40
        content = resp.json() if 'application/json' in resp.headers.get('Content-Type', '') else resp.content
        logger.log(level=level, msg=f"Status code: {resp.status_code}, Server msg: {content}")

    def handle_errors(self, resp: Response, **kwargs) -> Response:  # pylint: disable=W0613
        """
        Handle various HTTP errors here.

        Args:
            resp (Response): Response object

        Returns:
            retried_request (Response): The retried request.

        Raises:
            HTTPError: raises on 4xx, 5xx status codes, excluding 401.
        """
        if resp.status_code == requests.codes.unauthorized:  # pylint: disable=E1101
            logger.warning("Unauthorized error. Try obtaining or refreshing the API token.")
            # try logging in with env variables
            try:
                init()
            except ValueError:
                resp.raise_for_status()

            resp.request.headers['Authorization'] = self.headers['Authorization']
            resp.request.hooks['response'] = [self.log_response]
            retried_request = self.send(resp.request)
            return retried_request

        resp.raise_for_status()

    def set_token(self, token):
        self.headers['Authorization'] = f"Bearer {token}"


def init():
    """
    Login with environment variables.

    Raises:
        ValueError: When either username or password was not given.

    Returns:
        login(): Calls login with environment username and password.
    """
    import inferex
    project_root = os.path.abspath(os.path.dirname(inferex.__file__))
    inferex_file = Path(project_root) / ".inferex"
    load_dotenv(inferex_file)
    username = os.getenv("INFEREX_USERNAME")
    password = os.getenv("INFEREX_PASSWORD")
    if username is None or password is None:
        logger.warning("Username or password was not supplied or present in env.")
        raise ValueError("No username or password provided or present in env.")

    return login(username=username, password=password)


def login(**kwargs):
    """
    Log in with username and password to fetch an API token.

    Update session with new token.

    Args:
        username (str): User's username.
        password (str): User's password.

    Raises:
        RequestsException, HTTPError: When the request fails.

    Returns:
        return_code(int): 0 if response succeeded
    """
    if kwargs.get('username') is None or kwargs.get('password') is None:
        return init()

    # Run login & handle request exceptions
    try:
        response = requests.post(f"{settings.base_url}/login", data=kwargs)
    except RequestException:
        raise

    # Handle bad status code
    if not response.ok:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            logger.error(f"HTTP error on request - {exc}")
            raise

    # Get access token from response
    if token := response.json().get("access_token"):
        settings.write_token(token)
        api_session.set_token(token)

    return 0


def start_progress_bar(data: Union[dict, MultipartEncoderMonitor]):
    """
    Display a progress spinner while the request is in progress.

    Args:
        data (Union[MultipartEncoderMonitor, None], optional): A dict or monitor object.

    Returns:
        progress_bar: A progress bar object or a no-op object with a .close() method.
    """
    # If being piped
    if not sys.stdout.isatty():
        return create_patched_progress_bar()

    if isinstance(data, MultipartEncoderMonitor):
        # TODO: make progress bar show fully complete after upload is done (even for small payloads)
        progress_bar = tqdm(
            desc="☁️  Uploading",
            total=data.bundle_size,
            unit="B",
            unit_scale=True,
            ncols=80,
            leave=False,
            colour="green"
        )
        data.callback = lambda monitor: progress_bar.update(monitor.bytes_read - progress_bar.n)
    else:
        # TODO: make spinner logs disappear after it's finished
        progress_bar = yaspin.yaspin(text="Waiting on server response...", color=SPINNER_COLOR)
        progress_bar.close = progress_bar.stop
        progress_bar.start()

    return progress_bar


def create_patched_progress_bar():
    return type("", (object,), {'close': lambda _: None})()


def create_multipart_encoder_monitor(path: str, file: BinaryIO) -> MultipartEncoderMonitor:
        """
        Creates a MultipartEncoderMonitor instance to stream data on uploads
        and create a progress bar with.

        Args:
            path (str): path to file.
            file (BinaryIO): the file-like object to upload.

        Returns:
            monitor (MultipartEncoderMonitor): The encoder monitor to use as data in requests.
        """
        encoder = MultipartEncoder(
            fields = {"file": (path, file, "application/x-xz")}
        )
        monitor = MultipartEncoderMonitor(encoder, None)
        bundle_size = Path(path).stat().st_size
        monitor.bundle_size = bundle_size
        return monitor


api_session = ApiClientSession(settings.base_url, settings.api_token)
