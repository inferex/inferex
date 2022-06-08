""" Authentication sub-app.

This will be responsible for all API authentication methods username/password and/or API key
"""
import sys
from typing import Optional

import requests
import typer
from yaspin import yaspin
from inferex.api.client import OperatorClient
from inferex.io.termformat import SPINNER_COLOR, error, info, success
from inferex.io.token import cache_token
from inferex.settings import DEBIAN_FRONTEND


login_app = typer.Typer(help="🔑 Fetches your API key from the server.")


@login_app.callback(invoke_without_command=True)
def login(
    username: Optional[str] = typer.Option(None, "--username", "-u"),
    password: Optional[str] = typer.Option(None, "--password", "-p"),
):
    """Fetch api key via username & password authentication.

    Args:
        username: Inferex account username
        password: Inferex account password

    Raises:
        Exit: Typer exit code 1 on critial error
    """
    # Disable the no-member warning generated by requests
    # pylint: disable=no-member

    # password passed in via stdin
    if password == "-":  # nosec
        password = sys.stdin.read().strip()

    if DEBIAN_FRONTEND:
        # non-interactive mode is set, but username or password was not supplied
        if not username or not password:
            error("Username or password not supplied, exiting.")
            raise typer.Exit(1)
    else:
        if not username:
            username = typer.prompt("🧍 Inferex Username")
        if not password:
            password = typer.prompt("🔑 Inferex Password", hide_input=True)

    with yaspin(color=SPINNER_COLOR) as _:

        client = OperatorClient()

        try:
            auth_response = client.login(username, password)
        except requests.exceptions.ConnectionError as conn_err:
            error(str(conn_err))
            info(
                "\nYou can set the INFEREX_API_ROOT environment "
                "varible to point to a different server, "
                f"current config is: {client.api_root}\n"
            )
            raise typer.Exit(1)

    if auth_response.status_code == requests.codes.ok:
        # Convert to json
        auth_response_json = auth_response.json()

        # Store the token
        cache_token(auth_response_json)
        success("Login OK\n")

    elif auth_response.status_code == requests.codes.forbidden:
        error(f"Invalid Login, status code: {auth_response.status_code}")

    else:
        error(f"Server returned status code: {auth_response.status_code}")