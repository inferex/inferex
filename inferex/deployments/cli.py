""" CLI commands for deployments. """
import sys
from typing import Optional

import click
from pathlib import Path

from inferex.api.client import Client
from inferex.io.output import output_option, OutputType, handle_output
from inferex.io.utils import get_project_config


@click.group("deployment")
def commands():
    """
    🌎 Manage Inferex deployments.

    `inferex deployment <subcommand>
    """


@commands.command("get")
@click.argument("git_sha")
@output_option
def get(git_sha: str, output: OutputType):
    """
    Get deployment status by its git sha.
    \f
    Args:
        git_sha (str): The git sha of the deployment.
    """
    params = {'git_sha': git_sha}

    # Get deployments & print the data.
    client = Client()
    response_data = client.get(
        "deployments",
        params=params
    ).json()

    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)
        sys.exit(0)
    if not response_data and output == OutputType.TABLE:
        # temp/hotfix until jsonapi.org spec is implemented
        click.echo(f"No deployments found. <git_sha:{git_sha}>")
        sys.exit(0)

    handle_output(response_data, output, "deployments")


@commands.command("delete")
@output_option
@click.argument("deployment_id")
def delete(deployment_id: int, output: OutputType):
    """
    Delete a deployment by ID.
    \f

    Args:
        deployment_id (int): The ID of the deployment.
        output (str): The output format. Defaults to "table".
    """
    # Get operator client and GET deployments. Print the response.
    response_data = Client().delete(
        "deployments",
        params={"deployment_id": deployment_id}
    ).json()
    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)

    handle_output(response_data, output, "deployments")


@commands.command("ls")
@click.argument("git_sha", required=False)
@click.option("--project")
@output_option
@click.pass_context
def list_(
    ctx: click.Context,
    git_sha: Optional[str],
    project: Optional[str],
    output: OutputType
):
    """
    \b
    List a user's deployments.

    `inferex deployment ls (--project myproject)` -> all deployments (of myproject)
    """
    ctx.invoke(deployments, git_sha=git_sha, project=project, output=output)


@click.command("deployments", hidden=True)
@click.option("--project", default=None)
@click.argument("git_sha", required=False)
@output_option
def deployments(
    project: Optional[str],
    git_sha: Optional[str],
    output: OutputType
):
    """\b
    `inferex deployments` -> list of a user's deploymnets.

    \f
    Args:
        project (str, optional): The project to list deployments of.
        git_sha (str): Git sha of a deployment.
        output (str, optional): The output format. Defaults to "table".
    """
    params = {}
    if git_sha:
        params["git_sha"] = git_sha
    if project:
        project_config = get_project_config(project)
        project_name = project_config.get("project", {}).get("name", project)
        params["project_name"] = project_name

    # Get deployments & print the data.
    client = Client()
    response_data = client.get(
        "deployments",
        params=params
    ).json()

    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)
        sys.exit(0)
    if not response_data and output == OutputType.TABLE:
        # temp/hotfix until jsonapi.org spec is implemented
        click.echo(f"No deployments found. <git_sha:{git_sha}>, <project:{project}>")
        sys.exit(0)

    handle_output(response_data, output, "deployments")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
