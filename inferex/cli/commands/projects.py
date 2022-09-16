"""
    CLI commands for projects.
"""
import sys
from typing import Optional

import click

from inferex.sdk.resources import project
from inferex.utils.io.output import OutputFormat, output_option, handle_output
from inferex.utils.io import get_project_config
from inferex.utils.io import error


@click.group("project")
def commands():
    """
    🌎  Manage Inferex projects.
    """

@commands.command("get")
@click.argument("project_name")
@output_option
def get(project_name: int, output: Optional[OutputFormat]):
    """
    Get project status by its NAME.

    \f
    Args:
        index (str): The index of the project.
    """
    response = project.list(project_name)
    if not response.ok:
        error(
            f"""Something went wrong with the request.
                Status code: {response.status_code}
                Message: {response.json()}"""
        )
        sys.exit()

    response_data = response.json()
    if not response_data and output == OutputFormat.table:
        # temp/hotfix until jsonapi.org spec is implemented
        click.echo(f"No deployments found for <project_name:{project_name}>")
        sys.exit()

    handle_output(response_data, output, "projects")


@commands.command("delete")
@click.argument("indices", nargs=-1)
@click.option("-all", "-a", "--delete-all", is_flag=True)
@click.option("--force", is_flag=True, prompt="Some projects may have running deployments. Are you sure you want to delete them?")
@output_option
def delete(indices: str, delete_all: bool, force: bool, output: Optional[OutputFormat]):
    """
    Delete a project by INDEX.

    \f
    Args:
        indices(str): The list of INDEX's of the project.
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
        indices = [proj["id"] for proj in response.json()]

    deleted_projects = []
    for index in indices:
        response = project.delete(index)
        if not response.ok:
            error(
                f"""Something went wrong with the deleting id:{index}.
                    Status code: {response.status_code}
                    Message: {response.json()}"""
            )
            continue
        deleted_projects.append(response.json())

    handle_output(deleted_projects, output, "projects")


@click.command("projects", hidden=True)
@click.option("--project-name", help="Filter on a project name")
@output_option
def projects(
    project_name: Optional[str],
    output: Optional[OutputFormat],
):
    """
    📁  Get a list of projects.

    \f
    Args:
        project_name (str): Project name or path to project folder.
        output (str): The output format. Defaults to "table".
    """
    if project_name:
        project_config = get_project_config(project_name)
        # Get project name from argument or project config file.
        # project name can be a path or the project's name
        project_name = project_config.get("project", {}).get("name", project_name)

    response = project.list(name=project_name)
    if not response.ok:
        error(
            f"""Something went wrong with listing projects.
                Status code: {response.status_code}
                Message: {response.json()}"""
        )
        sys.exit()

    handle_output(response.json(), output, "projects")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
