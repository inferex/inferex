"""
    CLI commands for pipelines.
"""
from typing import Optional

import click

from inferex.sdk.resources import pipeline
from inferex.utils.io.output import handle_output, output_option, OutputFormat
from inferex.utils.io import error
from inferex.cli.utils import fetch_and_handle_response


URL_PATH = "pipelines"

@click.command("pipelines")
@click.argument("git_sha")
@output_option
def pipelines(
    git_sha: str,
    output: Optional[OutputFormat],
):
    """
    📞  List pipelines for a deployment.

        'inferex pipelines <git_sha>' -> pipelines of a deployment having <git_sha>.

    \f
    Args:
        git_sha (str): The git sha of a deployment.
        output (str): The output format. Defaults to "table".
    """
    response_data = fetch_and_handle_response(pipeline.list, URL_PATH, git_sha)
    handle_output(response_data, output, URL_PATH)
