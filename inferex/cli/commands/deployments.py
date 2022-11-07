"""
    CLI commands for deployments.
"""
from typing import Optional, Tuple

import click

from inferex.sdk.resources import deployments
from inferex.cli.display import output_option, OutputFormat, handle_output
from inferex.cli.terminal_format import error
from inferex.common.project import get_project_config
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "deployments"

@click.group("deployment")
def commands():
    """
    🌎  Manage Inferex deployments
    """

@commands.command("get")
@click.argument("deployment_sha")
@output_option
def get(deployment_sha: str, output: Optional[OutputFormat]):
    """
    Get deployment status by deployment sha

    \f
    Args:
        deployment_sha (str): The deployment sha of the deployment.
    """
    response_data = fetch_and_handle_response(
        func=deployments.get,
        path=URL_PATH,
        git_sha=deployment_sha
    )
    handle_output(response_data, output, URL_PATH)


@commands.command("delete")
@click.argument("deployment_shas", nargs=-1, required=False)
@click.option("--all", "-a", is_flag=True, help="Delete all deployments.")
@click.option(
    "--force",
    is_flag=True,
    prompt="Are you sure you want to delete the specified deployment(s)?",
    help="Force the deletion of deployment."
)
@output_option
def delete(deployment_shas: Tuple[str], all: bool, force: bool, output: Optional[OutputFormat]):
    """
    Delete deployment by deployment SHA

    \f
    Args:
        deployment_shas (str): The SHA of the deployment.
        output (str): The output format. Defaults to "table".
    """
    if not force:
        click.echo("Aborting delete.")
        return

    if all:
        # get all of the deployments instead of having to manually pass them in
        response_data = fetch_and_handle_response(deployments.get, URL_PATH)
        deployment_shas = [deployment.get('git_sha') for deployment in response_data]

    deleted_deployments = []
    for deployment_sha in deployment_shas:
        try:
            response_data = fetch_and_handle_response(
                func=deployments.delete,
                path=URL_PATH,
                exit_on_error=False,
                deployment_sha=deployment_sha,
            )
        except Exception as exc:
            error(f"Deleting {deployment_sha} could not complete - {exc}")
            continue
        deleted_deployments.append(response_data)

    if deleted_deployments:
        handle_output(deleted_deployments, output, URL_PATH)


@commands.command("ls")
@click.argument("deployment_sha", required=False)
@click.option("--project", default=None, help="Filter deployments by project name.")
@output_option
@click.pass_context
def list_(
    ctx: click.Context,
    deployment_sha: Optional[str],
    project: Optional[str],
    output: Optional[OutputFormat]
):
    """
    \b
    List user deployments

    \b
    Aliases: deployments, deploy ls
    \f
    Args:
        ctx: click.Context object.
        deployment_sha: Deployment sha of a deployment.
        project (str, optional): The project to list deployments of.
        output (str, optional): The output format. Defaults to "table".
    """
    ctx.invoke(deployments_list, deployment_sha=deployment_sha, project=project, output=output)


@click.command("deployments", hidden=True)
@click.option(
    "--project",
    default=None,
    help="Filter deployments by project name."
)
@click.argument("deployment_sha", required=False)
@output_option
def deployments_list(
    project: Optional[str],
    deployment_sha: Optional[str],
    output: Optional[OutputFormat]
):
    """
    \b
    List user deployments

    \f
    Args:
        project (str, optional): The project to list deployments of.
        deployment_sha (str): Deployment sha of a deployment.
        output (str, optional): The output format. Defaults to "table".
    """
    if project:
        project_config = get_project_config(project)
        project = project_config.get("project", {}).get("name", project)

    response_data = fetch_and_handle_response(
        func=deployments.get,
        path=URL_PATH,
        git_sha=deployment_sha,
        project_name=project
    )
    handle_output(response_data, output, URL_PATH)


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
