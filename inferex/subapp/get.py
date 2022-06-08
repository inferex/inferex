""" Get sub-app

Calls /projects/ endpoints for information about projects, deployments, and their activity.

inferex get deployments
> formatted table

inferex get deployment
> formatted table


inferex get <resource> <id>
inferex get deployment bodahbfoa

"""
import re
from typing import Optional

import typer
from tabulate import tabulate

from inferex.api.client import OperatorClient
from inferex.io.table import (
    get_project_display,
    get_deployment_display,
    get_endpoint_display,
)
from inferex.io.utils import get_project_params

# Regex
ip_address_pattern = re.compile(r"(10\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

# CLI
get_app = typer.Typer(help="🌎 Get information about Inferex resources.")


@get_app.command(
    "project",
    help="Get information about a project",
)
def get_project(
    project: Optional[str] = typer.Argument(None, help="Name or path of the project."),
):
    """Get information about a project by name.

    Args:
        project (Optional[str], optional): The name of the project.
    """
    # Get operator client
    client = OperatorClient()

    # Get project params
    params = get_project_params(project)

    # Get projects
    response_data = client.get("/projects", params=params)

    # Print response
    display_data = get_project_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)


@get_app.command(
    "projects",
    help="Get information about all projects",
)
def get_projects():
    """Get a list of projects for a user"""

    # Get operator client
    client = OperatorClient()

    # Get projects
    response_data = client.get("/projects")

    # Print response
    display_data = get_project_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)


@get_app.command(
    "deployment",
    help="Get information about a deployment",
)
def get_deployment(
    deployment: int = typer.Argument(None, help="ID of the deployment (required)."),
):
    """Get information about a single deployment by ID.

    Args:
        deployment (int, optional): The ID of the deployment.
    """
    # Get operator client
    client = OperatorClient()

    # Get deployments
    response_data = client.get("/deployments", params={"deployment_id": deployment})

    # Print response
    display_data = get_deployment_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)


@get_app.command(
    "deployments",
    help="Get information about all deployments",
)
def get_deployments(
    project: Optional[str] = typer.Argument(None, help="Name or path of the project."),
):
    """Gets a list of deployments from a project

    Args:
        project (Optional[str], optional): The project name or path
    """
    # Get operator client
    client = OperatorClient()

    # Get project params
    params = get_project_params(project)

    # Get deployments
    response_data = client.get("/deployments", params=params)

    # Ensure response_data exist
    if not response_data:
        typer.echo(f"No deployments found with project name '{project}'.")

    # Print response
    display_data = get_deployment_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)


@get_app.command(
    "endpoint",
    help="Get information about an endpoint",
)
def get_endpoint(
    endpoint: int = typer.Argument(..., help="ID of the endpoint (required)."),
):
    """Gets a single endpoint by ID.

    Args:
        endpoint (int, optional): The ID of the endpoint.
    """
    # inferex get endpoint <endpoint> -> find an endpoint by id

    # Get operator client
    client = OperatorClient()

    # Get endpoints
    response_data = client.get("/endpoints", params={"endpoint_id": endpoint})

    # Print response
    display_data = get_endpoint_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)


@get_app.command(
    "endpoints",
    help="Get information about all endpoints",
)
def get_endpoints(
    deployment: int = typer.Argument(..., help="ID of a deployment."),
):
    """Gets a list of endpoints for a deployment

    Args:
        deployment (int, optional): The ID of a deployment.
    """
    # inferex get endpoints <deployment_id> -> find all endpoints for a deployment
    # inferex get endpoints <path>         -> find all endpoints in the current directory

    # Get operator client
    client = OperatorClient()

    # Get deployments
    response_data = client.get("/endpoints", params={"deployment_id": deployment})

    # Print response
    display_data = get_endpoint_display(response_data)
    table = tabulate(display_data, headers="keys", tablefmt="plain")
    typer.echo(table)
