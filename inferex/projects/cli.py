""" CLI commands for projects. """
from typing import Optional

import click

from inferex.api.client import Client
from inferex.io.output import OutputType, output_option, handle_output
from inferex.io.utils import get_project_config


@click.group("projects", invoke_without_command=True)
@click.argument("argument", required=False)
@output_option
def commands(
    argument: str,
    output: Optional[OutputType],
):
    """\b
    📁 Manage Inferex projects. Optionally filter on a specific project.

    'inferex projects` -> list of projects
    `inferex project myproject` -> information for 'myproject'
    `inferex project 123 delete` -> Delete a project with ID 123 (TBD)

    \f
    Args:
        argument (str): Project name or path to project folder.
        output (str): The output format. Defaults to "table".
    """
    # Get project name from argument or project config file.
    params = {}
    if argument:
        project_config = get_project_config(argument)
        project_name = project_config.get("project", {}).get("name", argument)
        params["project_name"] = project_name

    # Get projects & print response data
    client = Client()
    response_data = client.get(
        "projects",
        params=params
    ).json()
    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)

    handle_output(response_data, output, "projects")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
