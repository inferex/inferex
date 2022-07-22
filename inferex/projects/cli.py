""" CLI commands for projects. """
from typing import Optional

import click

from inferex.api.client import Client
from inferex.io.output import OutputType, output_option, handle_output
from inferex.io.utils import get_project_config


@click.group("projects", invoke_without_command=True)
@click.pass_context
@click.argument("project_id", required=False)
@click.option("--project", default=None, help="Name or path of the project.")
@output_option
def commands(
    ctx: click.Context,
    project_id: Optional[int],
    project: Optional[str],
    output: Optional[OutputType],
):
    """\b
    📁 Manage Inferex projects. Optionally filter on a specific project.
    \b
    'inferex projects` -> list of projects
    `inferex project 123 delete` -> Delete a project with ID 123 (TBD)
    \f

    Args:
        ctx: click.Context object
        project_id (int): Project ID.
        project (str): The name or path of the project.
        output (str): The output format. Defaults to "table".
    """
    if project_id in commands.commands:
        click.echo("This command is invoked like `inferex projects 123 delete'")
    elif ctx.invoked_subcommand is None:
        client = Client()
        # Get project name from option or project config file.
        params = {}
        if project:
            project_config = get_project_config(project)
            project_name = project_config.get("project", {}).get("name", project)
            params.update({"project_name": project_name})

        # Get projects & print response data
        response_data = client.get(
            "projects",
            params=params
        ).json()
        if "errors" in response_data:
            click.echo(response_data.get("errors"), err=True)

        handle_output(response_data, output, "projects")
    else:
        # pass through to subcommands
        ctx.ensure_object(dict)
        ctx.obj['parameter'] = project_id


@commands.command("delete")
@click.pass_context
@click.option("--project_id")
@output_option
def delete(ctx: click.Context, project_id: int):
    """ Delete a project.

    Args:
        ctx: click.Context object
        project_id (int): Project ID.
    """
    if ctx:
        project_id = ctx.obj.get('parameter')

    # TODO: implement
    click.echo(f"TODO: delete {project_id}")


@commands.command("logs")
@click.pass_context
@click.option("--project-name")
@output_option
def logs(ctx: click.Context, project_name: str):
    """ Get a project's logs.

    Args:
        ctx: click.Context object
        project_name (str): Name of project.
    """
    if ctx:
        project_name = ctx.obj.get('parameter')

    # TODO: implement
    click.echo(f"TODO: get logs for {project_name}")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
