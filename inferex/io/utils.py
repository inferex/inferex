""" General IO utils """

from pathlib import Path
from datetime import datetime, timezone

import yaml
import humanize
from typer import Exit

from inferex.template.validation import ConfigInvalid, validate_project_file
from inferex.io.termformat import error, info


def bundle_size(size_bytes: int, decimal_places=2) -> str:
    """Convert an integer number of bytes to a human readable filesize

    Args:
        size_bytes (int): The filesize in bytes
        decimal_places (int): How many decimal places to round the result to

    Returns:
        str: The human readable string showing the size and units
    """
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:

        if size_bytes < 1024.0 or unit == "PiB":
            break

        size_bytes /= 1024.0

    return f"{size_bytes:.{decimal_places}f} {unit}"


def normalize_project_dir(path: str) -> Path:
    """Convert a user-supplied project path to a normalized form

    The supplied path can either be:

    A directory:        /home/sally/my_cool_project
    An inferex.yaml     /home/sally/my_cool_project/inferex.yaml

    Args:
        path (str): A full path to the project directory

    Returns:
        Path: A Path object to the directory component only
    """

    project_path = Path(path)

    if project_path.is_file():
        return project_path.parent

    return project_path


def valid_inferex_project(path: Path):
    """Checks to see if the project is a valid Inferex project

    For now, this function only checks to see if there's an
    inferex.yaml file inside the project folder. In future, this should really
    open the configuration file and validate its contents

    Args:
        path (Path): A path to an Inferex project folder

    Raises:
        ConfigInvalid: If the configuration file does not exist or fails schema validation
    """

    config_filepath = path / "inferex.yaml"

    if not config_filepath.is_file():
        raise ConfigInvalid("file does not exist")

    validate_project_file(config_filepath)


def read_project_config(full_path: Path) -> dict:
    """Reads a project config from path.

    Args:
        full_path (Path): path

    Raises:
        yaml_excep: YAMLError

    Returns:
        dict: dict
    """
    with open(full_path / "inferex.yaml", "r", encoding="utf-8") as stream:
        try:
            project_dict = yaml.safe_load(stream)
        except yaml.YAMLError as yaml_excep:
            error(yaml_excep)
            raise yaml_excep
    return project_dict


def get_project_name(full_path: Path) -> str:
    """Read inferex.yaml and return the project:name
        note: Project names should not be changed after creation.
              If a new name is desired, it is recommended to init a new project.

    Args:
        full_path (Path): absolute path to the .yaml file

    Returns:
        project name (str): name of the project

    Raises:
        Exit: Typer exit on critial failure
        yaml.YAMLError: On schema validation failure
    """

    # Read the config file
    project_dict = read_project_config(full_path=full_path)

    # Validate the config file
    project_name = project_dict.get("project", {}).get("name", {})
    if project_name:
        return project_name

    error(f"No project:name found in {full_path}")
    raise Exit(1)


def handle_api_response(response):
    """Convenience function for handling API responses.

    Checks if the request was successful and if it contains JSON data before calling
    the .json() function.

    Args:
        response (requests.Response): requests response object

    Returns:
        response.json(): json data if response was returned, otherwise exit.

    Raises:
        Exit: Exit code of 1 if json data is not indicated in headers.
    """

    if not response.ok:
        try:
            response_json = response.json()
            detail = response_json.get("detail", "No detail provided")
        except ValueError:
            detail = str(response.content)
        error(f"""{response.status_code} response from server.
            Detail: {detail}""")
        raise Exit(1)


    if "json" not in response.headers.get("content-type"):
        info("No JSON data was returned.")
        # exit with non-zero, as the command could be part of a chain of commands
        raise Exit(1)

    return response.json()



def get_datetime_age(timestamp: str) -> str:
    """
    Get the age of a datetime string relative to local timezone.

    Args:
        timestamp (str): The datetime string.

    Returns:
        str: The age of the datetime string.
    """
    if not timestamp:
        return timestamp

    # Parse the datetime string
    utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")

    # Get the timezone offset
    timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()

    # Convert UTC to local time
    current_age = utc_time + timezone_offset

    return humanize.naturaltime(current_age)


def get_project_params(project: str) -> dict:
    """Get a project_name from a project directory.

    Args:
        project (str): The path or name of the project.

    Returns:
        dict: The project name.
    """
    if not project:
        params = {}

    elif Path(project).exists():
        project_dir = normalize_project_dir(project)
        project_config = read_project_config(project_dir)
        project_name = project_config.get("project").get("name")
        params = {"project_name": project_name}
    else:
        params = {"project_name": project}
    return params
