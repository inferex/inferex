""" CLI commands for deployments. """
from typing import Optional

import click

from inferex.api.client import Client
from inferex.io.output import output_option, OutputType, handle_output
from inferex.io.utils import get_project_config


@click.group("deployments", invoke_without_command=True)
@click.pass_context
@click.option("--project", default=None)
@click.argument("deployment_id", default=None, required=False)
@output_option
def commands(
    ctx: click.Context,
    project: Optional[str],
    deployment_id: Optional[int],
    output: OutputType
):
    """\b
    🌎 Manage Inferex deployments.

    \b
    `inferex deployments` -> list of user's deploymnets
    `inferex deployment 123 delete` -> delete deployment with ID 123
    \f

    Args:
        ctx: click.Context object
        project (Optional[str], optional): The project name or path.
        deployment_id (int): ID of target deployment.
        output (str, optional): The output format. Defaults to "table".
    """
    # Click group that can be invoked without command, or with sub-commands
    if deployment_id in commands.commands:
        click.echo("This command is invoked like 'inferex deployment 123 delete`")
    elif ctx.invoked_subcommand is None:
        # Get operator client
        client = Client()
        params = {}
        if deployment_id:
            params.update({"deployment_id": deployment_id})

        # Get project params
        if project:
            project_config = get_project_config(project)
            project_name = project_config.get("project", {}).get("name", project)
            params.update({"project_name": project_name})

        # Get deployments & print the data.
        response_data = client.get(
            "deployments",
            params=params
        ).json()
        if "errors" in response_data:
            click.echo(response_data.get("errors"), err=True)
        if not response_data and output == OutputType.TABLE:
            # temp/hotfix until jsonapi.org spec is implemented
            click.echo(f"No deployments found. <deployment_id:{deployment_id}>, <project:{project}>")

        handle_output(response_data, output, "deployments")
    else:
        # pass through command to subcommands
        ctx.ensure_object(dict)
        ctx.obj["deployment_id"] = deployment_id  # save to context


@commands.command("delete")
@output_option
@click.option("--deployment_id")
@click.pass_obj
def delete(ctx: click.Context, deployment_id: int, output: OutputType):
    """
    Delete a deployment by ID.
    \f

    Args:
        ctx: click.Context object
        deployment_id (int): The ID of the deployment.
        output (str): The output format. Defaults to "table".
    """
    if ctx:
        # command passed through context
        deployment_id = ctx.get("deployment_id")

    click.echo(f"Deleting deployment <id:{deployment_id}>")

    # Get operator client and GET deployments. Print the response.
    response_data = Client().delete(
        "deployments",
        params={"deployment_id": deployment_id}
    ).json()
    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)

    handle_output(response_data, output, "deployments")


@commands.command("update")
@output_option
@click.option("--deployment_id")
@click.pass_obj
def update(ctx: click.Context, deployment_id: int):
    """ Update a deployment by ID.
    Args:
        ctx: click.Context object
        deployment_id (int): The ID of the deployment.
    """
    if ctx:
        # command passed through context
        deployment_id = ctx.get("deployment_id")
    # TODO: implement if needed
    click.echo(f"Updating deployment <id:{deployment_id}>")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
