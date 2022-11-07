"""
    CLI commands for pipelines.
"""
from typing import Optional

import click

from inferex.sdk.resources import pipelines
from inferex.cli.display import handle_output, output_option, OutputFormat
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "pipelines"

@click.group("pipeline")
def commands():
    """
    🏭  Manage Inferex pipelines
    """

@commands.command("ls")
@click.argument("deployment_sha")
@output_option
@click.pass_context
def list_(
    ctx: click.Context,
    deployment_sha: str,
    output: Optional[OutputFormat],
):
    """
    \b
    List deployment pipelines

    \b
    Aliases: pipelines, pipeline ls
    \f
    Args:
        ctx: click.Context object.
        deployment_sha (str): The deployment sha of a deployment.
        output (str): The output format. Defaults to "table".
    """
    ctx.invoke(pipelines_list, deployment_sha=deployment_sha, output=output)


@click.command("pipelines", hidden=True)
@click.argument("deployment_sha")
@output_option
def pipelines_list(
    deployment_sha: str,
    output: Optional[OutputFormat],
):
    """
    \b
    List deployment pipelines

    \f
    Args:
        git_sha (str): The git sha of a deployment.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(
        func=pipelines.list,
        path=URL_PATH,
        git_sha=deployment_sha
    )
    handle_output(response_data, output, URL_PATH)


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
