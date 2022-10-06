"""
    CLI commands for projects.
"""
import sys
from typing import Optional

import click

from inferex.sdk.resources import project
from inferex.utils.io.output import OutputFormat, output_option, handle_output
from inferex.utils.io import error
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "projects"

@click.group("project")
def commands():
    """
    🌎  Manage Inferex projects.
    """

@commands.command("get")
@click.argument("name")
@output_option
def get(name: str, output: Optional[OutputFormat]):
    """
    Get project status by name.

    \f
    Args:
        name (str): The name of the project.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(project.list, URL_PATH, name)
    handle_output(response_data, output, URL_PATH)


@commands.command("delete")
@click.argument("names", nargs=-1, required=False)
@click.option("-all", "-a", "--delete-all", is_flag=True)
@click.option("--force", is_flag=True, prompt="Some projects may have running deployments. Are you sure you want to delete them?")
@output_option
def delete(names: str, delete_all: bool, force: bool, output: Optional[OutputFormat]):
    """
    Delete a project by name.

    \f
    Args:
        names  (str): The list of names of the project.
        output (str): The output format. Defaults to "table".
    """
    if not force:
        return

    if delete_all:
        response = project.get()
        if not response.ok:
            error(
                f"""Something went wrong with fetching projects.
                    Status code: {response.status_code}
                    Message: {response.json()}"""
            )
            sys.exit()
        names = [proj["name"] for proj in response.json()]

    deleted_projects = []
    for name in names:
        response = project.delete(name)
        if not response.ok:
            error(
                f"""Something went wrong with the deleting of project: '{name}'.
                    Status code: {response.status_code}
                    Message: {response.json()}"""
            )
            continue
        deleted_projects.append(response.json())

    handle_output(deleted_projects, output, URL_PATH)


@click.command("projects", hidden=True)
@click.option("--name", help="Filter on a project name")
@output_option
def projects(
    name: Optional[str],
    output: Optional[OutputFormat],
):
    """
    📁  Get a list of projects.

    \f
    Args:
        name (str): Project name or path to project folder.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(project.list, URL_PATH, name)
    handle_output(response_data, output, URL_PATH)


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
