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
from typing import Union
from datetime import datetime, timezone

import typer

from inferex.api.client import OperatorClient

# Regex
ip_address_pattern = re.compile(r"(10\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

# CLI
logs_app = typer.Typer(help="🗒️ Get logs from Inferex deployments.")


def format_log(
    log: str,
    pod_name: str,
    container_name: str
) -> Union[str, None]:
    """Formats a log line

    Args:
        log (str): The log line to format
        pod_name (str): The name of the pod
        container_name (str): The name of the container

    Returns:
        Union[str, None]: The formatted log
    """
    # Skip redis & serve
    if container_name in ["redis", "serve"]:
        return None

    # Format timestamp
    timestamp, log = log.split(" ", 1)
    timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()
    timestamp_utc = datetime.strptime(timestamp[:-4], "%Y-%m-%dT%H:%M:%S.%f")
    timestamp_dt = timestamp_utc + timezone_offset
    timestamp = timestamp_dt.strftime("%H:%M:%S.%f")[:-3]

    # Format pod_name
    pod_name = pod_name.split("-")[-1]

    # Get verbosity
    verbosity = "I"
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        verbosity = level[0] if level in log else verbosity

    # Remove existing "INFO 54:32 >>"
    if ">>" in log:
        log = log.split(">>", 1)[1]

    # Remove IP addresses
    log = ip_address_pattern.sub("", log)

    # Remove double spacing
    log = " ".join(log.split())

    # Format log
    formatted_log = f"{timestamp} pod-{pod_name} {container_name} {verbosity}: {log}"
    return formatted_log


@logs_app.callback(invoke_without_command=True)
def get_logs(
    deployment: int = typer.Argument(..., help="ID of the deployment (required)."),
):
    """ inferex get logs <deployment> -> find logs by deployment id """

    # Get operator client
    client = OperatorClient()

    # Get endpoints
    response_data = client.get("/logs", params={"deployment_id": deployment})

    # Format logs
    logs = list(filter(
        lambda log: log is not None,
        (
            format_log(log, pod_name, container_name)
            for deployment in response_data.values()
            for pod_name, pod in deployment.items()
            for container_name, container in pod.items()
            for log in container.split('\n')
            if log
        )
    ))

    # Sort them by timestamp
    logs.sort()

    # Print response
    # TODO: color the logs!
    typer.echo('\n'.join(logs))
