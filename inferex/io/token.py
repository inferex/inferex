""" Utilities for handling the authentication tokens """
import json
from pathlib import Path

import typer

from inferex import __app_name__


def jwt_cache_path(app_name: str) -> Path:
    """Returns a path to the location where the JWT authentication token and
    API key is cached

    Args:
        app_name: The name of the cli APP used to build the path
                  for the config file, in our case "inferex"

    Returns:
        token_path (Path): The full path to the token json file location on filesystem
    """
    app_dir = typer.get_app_dir(app_name, force_posix=True)
    token_path = Path(app_dir) / "token.json"
    return token_path


def cache_token(token: dict):
    """Save the JWT token and API key to the filesystem cache

    Args:
        token: A dictionary containing the users OAuth token
    """
    # Get token cache path
    cache = jwt_cache_path(__app_name__)

    # Ensure directory exists
    cache.parent.mkdir(parents=True, exist_ok=True)

    # Write token to file
    with open(cache, "w", encoding="utf-8") as file_pointer:
        json.dump(token, file_pointer)


def cached_token() -> dict:
    """Read the JWT token and API key from the filesystem

    Returns:
        oauth_token (dict): The users OAuth token
    """
    cache = jwt_cache_path(__app_name__)

    if not cache.is_file():
        return None

    with open(cache, "r", encoding="utf-8") as file_pointer:
        oauth_token = json.load(file_pointer)
        return oauth_token
