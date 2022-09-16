"""
    CLI commands for pipelines.
"""
import sys
from typing import Optional

import click

from inferex.sdk.resources import pipeline
from inferex.utils.io.output import handle_output, output_option, OutputFormat
from inferex.utils.io import error


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
    response = pipeline.list(git_sha=git_sha)
    if not response.ok:
        error(
            f"""Something went wrong with listing pipelines.
                Status code: {response.status_code}
                Message: {response.json()}"""
        )
        sys.exit()

    handle_output(response.json(), output, "pipelines")
