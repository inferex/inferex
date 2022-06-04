""" Info sub-app

Calls /projects/ endpoints for information about projects, deployments, and their activity.
"""
from typing import Optional
import typer

from inferex.api.client import OperatorClient


info_app = typer.Typer(help="ℹ️ Get detailed information about projects.")
client = OperatorClient()


@info_app.command("get",
    help="Get information about all projects, or a specific one by passing in its name.")
def get(
    project_name: Optional[str] = typer.Argument(
    None,
    help="Name of your project."
    )
):
    """ Makes a GET request to the API server.

    Args:
        project_name: Optional name of project to get more detailed information about.
            Otherwise, list information about all projects.
    """
    if project_name is None:
        response_data = client.info("/projects")
    else:
        response_data = client.info(f"/projects/{project_name}/deployments")

    typer.echo(response_data)


@info_app.command("deployment", help="Get deployment details by its ID.")
def deployment(deployment_id: str):
    """
    Makes a GET request to the API server.

    Args:
        deployment_id: Database ID of the deployment.
    """
    typer.echo(client.info(f"/projects/deployments/{deployment_id}"))


@info_app.command("endpoint", help="Get endpoint details by its ID.")
def endpoint(endpoint_id: str):
    """
    Makes a GET request to the API server.

    Args:
        endpoint_id: Database ID of the endpoint.
    """
    typer.echo(client.info(f"/projects/endpoints/{endpoint_id}"))
