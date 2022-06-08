"""Table formatting"""
from typing import Union
from inferex.io.utils import get_datetime_age


def get_project_display(project_data: list) -> list:
    """Format a list of project data for display purposes.

    Args:
        project_data (list): The list to format.

    Returns:
        list: The formatted list
    """

    display_data = []
    for project in project_data:
        # Create display object
        display_data.append({
            "INDEX": project.get("id"),  # e.g. 42
            "NAME": project.get("name"),  # e.g. 'SimpleFunction'
            "AGE": get_datetime_age(project.get("added_at")),  # e.g. '5m ago'
        })
    return display_data


def get_deployment_display(deployment_data: Union[list, dict]) -> list:
    """Format a list of deployment data for display purposes.

    Args:
        deployment_data (list): The list to format.

    Returns:
        list: The formatted list
    """
    if isinstance(deployment_data, dict):
        deployment_data = [deployment_data]

    display_data = []
    for deployment in deployment_data:
        # Create display object
        display_data.append({
            "INDEX": deployment.get("id"),  # e.g. 42
            "PROJECT": deployment.get("project_name"),  # e.g. 'SimpleFunction'
            "STATUS": deployment.get("deployment_status"),  # e.g. 'deployed'
            "AGE": get_datetime_age(deployment.get("added_at", None)),  # e.g. '5m ago'
            "URL": (
                deployment.get("deployment_url") or
                deployment.get("repository_url")
            ),
            "VERSION": deployment.get("version"),  # e.g. '1.0.0'
            "SHA": deployment.get("git_sha"),  # e.g. '2794bd21'
        })
    display_data.reverse()
    return display_data


def get_endpoint_display(endpoint_data: list) -> list:
    """Format a list of endpoint data for display purposes.

    Args:
        endpoint_data (list): The list to format.

    Returns:
        list: The formatted list
    """

    display_data = []
    for endpoint in endpoint_data:
        # Create display object
        display_data.append({
            "INDEX": endpoint.get("id"),  # e.g. 42
            "DEPLOYMENT": endpoint.get("deployment_id"),  # e.g. 42
            "PROJECT": endpoint.get("project_name"),  # e.g. 'SimpleFunction'
            "STATUS": endpoint.get("deployment_status"),  # e.g. 'deployed'
            "AGE": get_datetime_age( # e.g. '5m ago'
                endpoint.get("added_at") or
                endpoint.get("edited_at")
            ),
            "PATH": endpoint.get("url"),
            "IS_ASYNC": bool(endpoint.get("is_async")),  # e.g. '2794bd21'
            "VERSION": endpoint.get("version"),  # e.g. '1.0.0'
            "SHA": endpoint.get("git_sha"),  # e.g. '2794bd21'
        })
    return display_data
