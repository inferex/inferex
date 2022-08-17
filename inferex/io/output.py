"""TABLE formatting"""

import re
import sys
import json
from typing import List, Union, Optional
from datetime import datetime, timezone
from enum import Enum

import yaml
import click
from tabulate import tabulate
from pygments import highlight, lexers, formatters

from inferex.io.utils import get_datetime_age


CONFIG_DISPLAY_TABLE = {
    "headers": "keys",
    "tablefmt": "plain",
}

# control what columns are displayed and in what order here
DISPLAY_COLUMNS = {
    'projects': ["id", "name", "added_at"],
    'deployments':[
        "git_sha", "project_name", "deployment_status", "added_at",
        "deployment_url", "version", "id"
        ],
    'endpoints': [
        "id", "git_sha", "project_name", "deployment_status",
        "added_at", "url", "version", "is_async"
        ],
}

# control what columns are renamed as here
KEY_MAPS = {
    'id': "INDEX",
    'added_at': "AGE",
    'edited_at': "AGE",
    'project_name': "PROJECT",
    'deployment_status': "STATUS",
    'deployment_url': "URL",
    'deployment_timestamp': "AGE",
    'repository_url': "URL",
    'git_sha': "SHA",
    'deployment_id': "DEPLOYMENT",
    'url': "PATH",
    'is_async': "ASYNC",
}

class OutputType(str, Enum):
    """ Class for click option output format. """
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"

# Regex for IP addresses
ip_address_pattern = re.compile(r"(10\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

# Formatter for yaml & json
pygments_formatter = formatters.TerminalFormatter()

def output_option(function):
    """ click decorator for specifying output format. """
    function = click.option(
        "--output",
        "-o",
        type=OutputType,
        default=OutputType.TABLE,
        help="table | json | yaml"
    )(function)
    return function

def format_display_data(
    api_data: Union[list, dict],
    endpoint: Optional[str] = None
    ) -> List[dict]:
    """Returns a list of dicts of formatted display data.

    Args:
        api_data (Union[list, dict]): The list of data to display.
        endpoint (str): The API endpoint the data is being returned from.

    Returns:
        List[dict]: The formatted display data.
    """

    # Default display is 1-1 mapping of data
    if not api_data:
        return []
    if isinstance(api_data, dict):
        api_data = [api_data]

    def sort_order_helper(item):
        """ Sorting function for ordering a dict. """
        if item[0] not in DISPLAY_COLUMNS.get(endpoint):
            return 0
        return DISPLAY_COLUMNS.get(endpoint).index(item[0])

    formatted_data = []
    for obj in api_data:
        # create a new dict with sorted, renamed keys
        new_data = {}
        if endpoint:
            # sort the keys
            obj = dict(sorted(obj.items(), key=sort_order_helper))
        for key, val in obj.items():
            if endpoint and key not in DISPLAY_COLUMNS.get(endpoint):
                continue
            if 'added' in key or 'edited' in key:
                val = get_datetime_age(val)
            # rename the keys
            new_data.update({KEY_MAPS.get(key) or key.upper(): val})

        formatted_data.append(new_data)

    return formatted_data


def table(data: Union[list, dict], endpoint: Optional[str] = None):
    """Prints a table of data.

    Args:
        data (Union[list, dict]): The data to display.
        endpoint (str): The endpoint the data has returned from.
    """

    display_data = format_display_data(data, endpoint)
    table_data = tabulate(display_data, **CONFIG_DISPLAY_TABLE)
    click.echo(table_data)


def handle_output(
    data: Union[list, dict],
    output: str,
    endpoint: Optional[str] = None
    ):
    """Handles outputting data.

    Args:
        data (Union[list, dict]): The data to output.
        output (str): The output format, one of 'table', 'json', or 'yaml.
        endpoint (str): The endpoint the data has returned from.
    """
    if output == OutputType.TABLE:
        table(data, endpoint)
    elif output == OutputType.JSON:
        data = json.dumps(data, indent=4, sort_keys=True)
        if sys.stdout.isatty(): # TODO: use isatty() in the click.echo for color
            data = highlight(
                data,
                lexers.JsonLexer(),
                pygments_formatter,
            )
        click.echo(data)
    elif output == OutputType.YAML:
        data = yaml.dump(data)
        if sys.stdout.isatty():
            data = highlight(
                data,
                lexers.YamlLexer(),
                pygments_formatter,
            )
        click.echo(data)


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
    # Format pod_name
    pod_name = pod_name.split("-")[-1]

    # Format timestamp
    timestamp, log = log
    timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()
    timestamp_utc = datetime.fromtimestamp(int(timestamp) // 1e9)
    timestamp = timestamp_utc + timezone_offset

    if " " not in log:
        return None

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
    formatted_log = (timestamp, f"pod-{pod_name} {container_name} {verbosity}: {log}")
    return formatted_log


def display_logs(data: dict):
    """Displays logs.

    Args:
        data (dict): The data to display.
    """

    # Format logs
    logs = list(filter(
        lambda log: log is not None,
        (
            format_log(log, pod_name, container_name)
            for namespace in data.values()
            for pod_name, pod in namespace.items()
            for container_name, container in pod.items()
            for log in container
            if log
        )
    ))

    # Sort them by timestamp
    sorted_logs = sorted(logs, key=lambda log: log[0].timestamp())

    # Print response
    # TODO: color the logs!
    for log in sorted_logs:
        timestamp = log[0].strftime("%H:%M:%S.%f")[:-3]
        click.echo(f"{timestamp} {log[1]}")
