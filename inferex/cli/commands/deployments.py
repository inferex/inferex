"""
    CLI commands for deployments.
"""
import sys
from typing import Optional

import click

from inferex.sdk.resources import deployment
from inferex.utils.io.output import output_option, OutputFormat, handle_output
from inferex.utils.io.utils import get_project_config, error
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "deployments"

@click.group("deployment")
def commands():
    """
    🌎  Manage Inferex deployments.
    """

@commands.command("get")
@click.argument("git_sha")
@output_option
def get(git_sha: str, output: Optional[OutputFormat]):
    """
    Get deployment status by its git sha.

    \f
    Args:
        git_sha (str): The git sha of the deployment.
    """
    response_data = fetch_and_handle_response(deployment.get, URL_PATH, git_sha)
    handle_output(response_data, output, URL_PATH)


@commands.command("delete")
@click.argument("deployment_shas", nargs=-1, required=False)
@click.option("--all", "all_", is_flag=True)
@click.option("--force", is_flag=True, prompt="Are you sure you want to delete specified deployment(s)?")
@output_option
def delete(deployment_shas: str, all_: bool, force: bool, output: Optional[OutputFormat]):
    """
    Delete a deployment by its git sha.

    \f
    Args:
        deployment_shas (str): The ID of the deployment.
        output (str): The output format. Defaults to "table".
    """
    if not force:
        click.echo("Aborting delete.")
        return

    if all_:
        # Get all the user's deployment ID's
        response = deployment.get()
        if not response.ok:
            error(
                f"""Something went wrong with the request.
                Status code: {response.status_code}
                Message: {response.json()}"""
            )
            sys.exit()
        deployment_shas = [ud.get('git_sha') for ud in response.json()]

    deleted_deployments = []
    for deployment_sha in deployment_shas:
        response = deployment.delete(deployment_sha)
        if not response.ok:
            error(
                f"""Something went wrong with deleting sha:{deployment_sha}.
                    Status code: {response.status_code}
                    Message: {response.json()}"""
            )
            continue
        deleted_deployments.append(response.json())

    handle_output(deleted_deployments, output, URL_PATH)


@commands.command("ls")
@click.argument("git_sha", required=False)
@click.option("--project")
@output_option
@click.pass_context
def list_(
    ctx: click.Context,
    git_sha: Optional[str],
    project: Optional[str],
    output: Optional[OutputFormat]
):
    """
    List a user's deployments. Filter by project with --project (can be a name or path).

    \f
    Args:
        ctx: click.Context object.
        git_sha: Git sha of a deployment.
        project (str, optional): The project to list deployments of.
        output (str, optional): The output format. Defaults to "table".
    """
    ctx.invoke(deployments, git_sha=git_sha, project=project, output=output)


@click.command("deployments", hidden=True)
@click.option("--project", default=None)
@click.argument("git_sha", required=False)
@output_option
def deployments(
    project: Optional[str],
    git_sha: Optional[str],
    output: Optional[OutputFormat]
):
    """
    List a user's deployments. Filter by project with --project (can be a name or path).

    \f
    Args:
        project (str, optional): The project to list deployments of.
        git_sha (str): Git sha of a deployment.
        output (str, optional): The output format. Defaults to "table".
    """
    if project:
        project_config = get_project_config(project)
        project = project_config.get("project", {}).get("name", project)

    response_data = fetch_and_handle_response(deployment.get, URL_PATH, git_sha, project)
    handle_output(response_data, output, URL_PATH)


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
