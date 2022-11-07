""" Functions for validating Inferex projects. """
import ast
import fnmatch
import os
from pathlib import Path
from typing import List, Union

from inferex.sdk.logs import get_logger


logger = get_logger(__name__)

VALID_PIPELINE_KWS = ['name', 'is_async', 'timeout', ]

def pre_walk_dir_check(path: str) -> None:
    """
    Check the to-be-deployed directory for .py files up to two levels deep.
    If there are none, raise an exception.

    Example: a user issues `inferex deploy` from their root directory. Instead
    of recursively walking all folders and files, exit early.

    Args:
        path(str): the project directory to check

    Raises:
        Exception: if there are no python files in the project dir, or in
                   subfolders 1 level beneath the project dir.
    """
    project_root_files = list(fnmatch.filter(os.listdir(path), "*.py"))
    project_root_folders = [p for p in os.listdir(path) if os.path.isdir(p)]
    subfolder_python_files = []
    for folder in project_root_folders:
        subfolder_python_files.extend(list(fnmatch.filter(os.listdir(folder), "*.py")))

    if not project_root_files and not subfolder_python_files:
        raise Exception(
            f"No python files found in or directly beneath {path}. "
            "Is this the right directory?"
        )



def get_python_filepaths(path: str) -> list:
    """ Given a directory, look for '*.py" files recursively and return a list
        of filepaths.

    Args:
        path(str): the project directory to check

    Returns:
        python_filepaths(list): a list of fullpaths to python files in the
            project directory.
    """
    pre_walk_dir_check(path)
    python_filepaths = []
    for root, _, filenames in os.walk(path):
        python_filepaths.extend(
            os.path.join(
                root, filename
            ) for filename in fnmatch.filter(filenames, "*.py")
        )

    return python_filepaths



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
