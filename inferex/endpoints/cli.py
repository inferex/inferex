"""
    Get information about endpoints.
"""
from typing import Optional

import click

from inferex import Client
from inferex.io.output import handle_output, output_option, OutputType


@click.group("endpoints", invoke_without_command=True)
@click.argument("git_sha")
@output_option
def commands(
    git_sha: str,
    output: Optional[OutputType],
):
    u"""\b
    📞 List endpoints for a deployment.

    'inferex endpoints <git_sha>' -> Endpoints of a deployment having <git_sha>.
    \f

    Args:
        git_sha (str): The git sha of a deployment.
        output (str): The output format. Defaults to "table".
    """
    # Get operator client and GET endpoints
    client = Client()
    response_data = client.get(
        "endpoints",
        params={"git_sha": git_sha}
    ).json()
    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)

    handle_output(response_data, output, "endpoints")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
