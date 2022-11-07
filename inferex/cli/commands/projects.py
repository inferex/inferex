"""
    CLI commands for projects.
"""
from typing import Optional, Tuple

import click

from inferex.sdk.resources import projects
from inferex.cli.display import OutputFormat, output_option, handle_output
from inferex.cli.terminal_format import error
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "projects"


@click.group("project")
def commands():
    """
    🌌  Manage Inferex projects
    """

@commands.command("get")
@click.argument("name")
@output_option
def get(name: str, output: Optional[OutputFormat]):
    """
    Get project status by name

    NAME: The name of the project.

    \f
    Args:
        name (str): The name of the project.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(
        func=projects.list,
        path=URL_PATH,
        name=name
    )
    handle_output(response_data, output, URL_PATH)


@commands.command("delete")
@click.argument("names", nargs=-1, required=False)
@click.option("--all", "-a", is_flag=True, help="Delete all projects.")
@click.option(
    "--force",
    is_flag=True,
    prompt="Some projects may have running deployments. Are you sure you want to delete the specified project(s)?",
    help="Force the deletion of project."
)
@output_option
def delete(names: Tuple[str], all: bool, force: bool, output: Optional[OutputFormat]):
    """
    Delete project by name

    \f
    Args:
        names  (tuple): An iterable of project names.
        output (str): The output format. Defaults to "table".
    """
    if not force:
        return

    if all:
        # get all project names instead of having to manually pass them in
        response_data = fetch_and_handle_response(projects.list, URL_PATH)
        names = [project.get('name') for project in response_data]

    deleted_projects = []
    for name in names:
        try:
            response_data = fetch_and_handle_response(
            func=projects.delete,
            path=URL_PATH,
            exit_on_error=False,
            name=name
        )
        except Exception as exc:
            error(f"Deleting project {name} could not complete - {exc}")
            continue
        deleted_projects.append(response_data)

    if deleted_projects:
        handle_output(deleted_projects, output, URL_PATH)


@commands.command("ls")
@click.option("--name", help="Filter projects by name or path.")
@output_option
@click.pass_context
def list_(
    ctx: click.Context,
    name: Optional[str],
    output: Optional[OutputFormat],
):
    """
    \b
    List user projects

    \b
    Aliases: projects, project ls
    \f
    Args:
        ctx: click.Context object.
        name (str): Project name or path to project directory.
        output (str): The output format. Defaults to "table".
    """
    ctx.invoke(projects_list, name=name, output=output)


@click.command("projects", hidden=True)
@click.option("--name", help="Filter projects by name or path.")
@output_option
def projects_list(
    name: Optional[str],
    output: Optional[OutputFormat],
):
    """
    \b
    List user projects

    \f
    Args:
        name (str): Project name or path to project directory.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(
        func=projects.list,
        path=URL_PATH,
        name=name
    )
    handle_output(response_data, output, URL_PATH)


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
