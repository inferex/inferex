""" General IO utils """
from typing import Union
from datetime import datetime, timezone
from pathlib import Path

import yaml
import humanize
from cerberus import Validator

from inferex.utils.io.termformat import error, info


class ConfigSchemaException(Exception):
    """ Exception to raise when errors are encountered in inferex.yaml validation. """

DEPLOYMENT_MEMORY_REGEX = r"(?P<value>\d+)(?:Gi|G)$"
DEPLOYMENT_CPU_REGEX = r"(?P<value>\d+)m?$"


CONFIG_SCHEMA = {
    "project": {
        "required": True,
        "type": "dict",
        "schema": {"name": {"required": True, "type": "string"}},
    },
    "scaling": {
        "required": False,
        "type": "dict",
        "schema": {
            "replicas": {"required": True, "type": "number", "min": 1, "max": 10},
            "memory": {
                "type": "string",

                "minlength": 2,
                "maxlength": 20,
                "regex": DEPLOYMENT_MEMORY_REGEX
            },
            "cpu": {
                "type": ["string", "number"],
                "minlength": 1,
                "maxlength": 20,
                "regex": DEPLOYMENT_CPU_REGEX
            },
        },
    },
}


default_project = {
    "project": {
        "name": "untitled"
    },
    "scaling": {
        "replicas": 1
    },
}

def get_project_config(project_path: Union[Path, None]) -> dict:
    """Read inferex.yaml and return the project dictionary

    Args:
        project_path (Union[Path, None]): path of the project.

    Returns:
        project_config (dict): the project config.

    Raises:
        yaml.YAMLError: Raised when loading inferex.yaml file.
        ConfigSchemaException: Raised when an inferex.yaml schema fails validation.
    """

    # Ensure the file exists
    config_path = Path(project_path) / "inferex.yaml"
    if not config_path.exists():
        return {}

    # Read the config file
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            project_config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        error(str(exc))
        raise exc

    # Validate the config file
    validator = Validator(CONFIG_SCHEMA)
    valid = validator.validate(project_config)
    if not valid:
        error("Project config file is invalid:")
        info(str(validator.errors))
        raise ConfigSchemaException

    return project_config


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

    # Parse the datetime string, split off microseconds
    utc_time = datetime.strptime(timestamp.split(".")[0], "%Y-%m-%dT%H:%M:%S")

    # Get the timezone offset
    timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()

    # Convert UTC to local time
    current_age = utc_time + timezone_offset

    return humanize.naturaltime(current_age)
