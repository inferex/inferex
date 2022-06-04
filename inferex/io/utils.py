""" General IO utils """
from pathlib import Path
import yaml

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


def get_project_name(full_path: Path) -> str:
    """ Read inferex.yaml and return the project:name
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
    with open(full_path / 'inferex.yaml', "r", encoding="utf-8") as stream:
        try:
            project_dict = yaml.safe_load(stream)
        except yaml.YAMLError as yaml_excep:
            error(yaml_excep)
            raise

    project_name = project_dict.get('project', {}).get('name', {})

    if project_name:
        return project_name

    error(f"No project:name found in {full_path}")
    raise Exit(1)


def handle_api_response(response):
    """ Convenience function for handling API responses.

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
        error(f"Non-200 response from server ({response.status_code})",
            msg_type="error")

    if "json" not in response.headers.get("content-type"):
        info("No JSON data was returned.", msg_type="info")
        # exit with non-zero, as the command could be part of a chain of commands
        raise Exit(1)

    return response.json()
