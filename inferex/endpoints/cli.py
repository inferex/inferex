"""
    Get information about endpoints.
"""
from typing import Optional

import click

from inferex import Client
from inferex.io.output import handle_output, output_option, OutputType


@click.group("endpoints", invoke_without_command=True)
@click.argument("deployment_id")
@output_option
def commands(
    deployment_id: Optional[int],
    output: Optional[OutputType],
):
    u"""\b
    📞 List endpoints for a deployment.

    'inferex endpoints <deployment_id>' -> list of endpoints of a deployment.
    \f

    Args:
        deployment_id (int): The ID of a deployment.
        output (str): The output format. Defaults to "table".
    """
    # Get operator client and GET endpoints
    client = Client()
    response_data = client.get(
        "endpoints",
        params={"deployment_id": deployment_id}
    ).json()
    if "errors" in response_data:
        click.echo(response_data.get("errors"), err=True)

    handle_output(response_data, output, "endpoints")


if __name__ == "__main__":
    commands()  # pylint: disable=E1120
