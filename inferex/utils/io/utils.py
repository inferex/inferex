""" General IO utils """
import ast
from typing import Union, List
from datetime import datetime, timezone
from pathlib import Path

import yaml
import humanize
from cerberus import Validator

from inferex.utils.io.termformat import error, info
from inferex.utils.io.logs import get_logger
from inferex.utils.io.scanning import get_python_filepaths


logger = get_logger(__name__)

class ConfigSchemaException(Exception):
    """ Exception to raise when errors are encountered in inferex.yaml validation. """

DEPLOYMENT_MEMORY_REGEX = r"(?P<value>\d+)(?:Gi|G)$"
DEPLOYMENT_CPU_REGEX = r"(?P<value>\d+)m?$"
VALID_PIPELINE_KWS = ['name', 'is_async', 'timeout', ]

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


def traverse_attribute(node: object) -> Union[str, None]:
    """
    Travel to the root name attribute and return a dotted name.

    Args:
        node(object): the ast node to traverse.

    Returns:
        string: the name/id of the node object.
    """
    if isinstance(node, ast.Attribute):
        return f"{traverse_attribute(node.value)}.{node.attr}"
    elif isinstance(node, ast.Name):
        return node.id


def parse_decorators(decorators: List[object]) -> List[str]:
    """
    Parse a list of decorators and check if they are valid inferex decorators.

    Args:
        decorators(list): a list of ast node objects.

    Raises:
        ValueError: If pipeline.py contains an invalid definition.

    Returns:
        pipeline_urls(list): a list of url paths defined in pipeline decorators.
    """
    pipeline_urls = []
    for decorator in decorators:
        if not isinstance(decorator, ast.Call):
            continue

        decorator_name = traverse_attribute(decorator.func)

        # not an inferex decorator
        if "pipeline" not in decorator_name:
            continue

        if len(decorator.args) > 0:
            raise ValueError("Arguments not supported")

        for keyword in decorator.keywords:
            pipeline_url = keyword.value.value
            if keyword.arg not in VALID_PIPELINE_KWS:
                raise ValueError(
                    f"Unsupported keyword in pipeline decorator. "
                    f"Supported keywords are: {', '.join(VALID_PIPELINE_KWS)}"
                )
            # check if name string is hyphenated alphanumeric
            if keyword.arg == "name":
                normalized_pipeline_url = pipeline_url.replace("_", "-").lower()
                if not normalized_pipeline_url.replace("-", "").isalnum():
                    raise ValueError(
                        f"Invalid pipeline name: {pipeline_url} "
                        "Pipeline names must be hyphenated alphanumeric strings"
                    )

                pipeline_urls.append(pipeline_url.lower())

    return pipeline_urls


def validate_pipelines(target_dir: Path) -> bool:
    """
    Walk python files in the project folder and parse their contents.
    Check if the definition is valid, and if not, raise and fail fast.

    Example invalid declaration (duplicate names):
        @pipeline(name="foo")
        ...function...

        @pipeline(name="foo")
        ...function...

    Example invalid pipeline (unsupported keyword):
        @pipeline(endpoint="foo")
        ...function...

    Example invalid pipeline (unsupported args):
        @pipeline("version-1", name="my-inference")
        ...function...

    Example invalid pipeline (bad name value):
        @pipeline(name="my-inference!")
        ...function...

    Args:
        target_dir(str): the directory to look for pipeline.py in.

    Raises:
        OSError: If reading pipeline.py failed.
    """
    python_filepaths = get_python_filepaths(target_dir)
    parsed_urls = []
    for path in python_filepaths:
        try:
            with open(path, "r") as f:
                source = f.read()
        except OSError:
            raise

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                parsed_urls.extend(parse_decorators(node.decorator_list))

    if len(set(parsed_urls)) < len(parsed_urls):
        raise ValueError("Pipeline names must be unique.")
