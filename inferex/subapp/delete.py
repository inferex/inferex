""" Delete sub-app
"""

import typer
from tabulate import tabulate

from inferex.api.client import OperatorClient
from inferex.io.table import get_deployment_display

# CLI
delete_app = typer.Typer(help="🗑️ Delete projects, deployments, and endpoints.")

@delete_app.command(
    "deployment",
    help="Delete a deployment by ID.",
)
def delete_deployment(
    deployment: int = typer.Argument(None, help="ID of the deployment (required)."),
):
    """Delete a deployment by ID.

    Args:
        deployment (int, optional): The ID of the deployment.
    """
    # Get operator client
    client = OperatorClient()

    # Get deployments
    response_data = client.delete("/deployments", params={"deployment_id": deployment})

    # Print response
    display_data = get_deployment_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)
