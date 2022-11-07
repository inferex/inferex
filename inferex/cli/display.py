""" Formatting raw data into tabular data in the terminal. """

import json
import re
import sys
from datetime import datetime, timezone
from enum import Enum, unique
from typing import List, Optional, Union

import click
import humanize
import yaml
from pygments import formatters, highlight, lexers
from tabulate import tabulate


CONFIG_DISPLAY_TABLE = {
    "headers": "keys",
    "tablefmt": "plain",
}

# control what columns are displayed and in what order here
DISPLAY_COLUMNS = {
    'projects': ["name", "added_at"],
    'deployments':[
        "git_sha", "project_name", "deployment_status", "added_at",
        "deployment_url", "version",
    ],
    'pipelines': [
        "git_sha", "project_name", "deployment_status",
        "added_at", "url", "version", "is_async",
    ],
}

# control what columns are renamed as here
KEY_MAPS = {
    'added_at': "AGE",
    'edited_at': "AGE",
    'project_name': "PROJECT",
    'deployment_status': "STATUS",
    'deployment_url': "DOMAIN",
    'deployment_timestamp': "AGE",
    'repository_url': "URL",
    'git_sha': "SHA",
    'url': "PATH",
    'is_async': "ASYNC",
}

TIME_HELP_TEXT = """How far back to query logs. E.g., '1h' = 1 hour, '1d' = 1 day...\n
s = seconds,
m = minutes,
h = hours,
d = days,
w = weeks
"""

# Regex for IP addresses
IP_ADDRESS_PATTERN = re.compile(r"(10\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

# Formatter for yaml & json
PYGMENTS_FORMATTER = formatters.TerminalFormatter()

@unique
class OutputFormat(str, Enum):
    """ Enumeration of available CLI output options. """
    table = "table"
    json = "json"
    yaml = "yaml"


def get_datetime_age(timestamp: str) -> str:
    """
    Get the age of a datetime string relative to local timezone.

    Args:
        timestamp (str): The datetime string.

    Returns:
        str: The age of the datetime string.
    """
    if not timestamp:
        return timestamp

    # Parse the datetime string, split off microseconds
    utc_time = datetime.strptime(timestamp.split(".")[0], "%Y-%m-%dT%H:%M:%S")

    # Get the timezone offset
    timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()

    # Convert UTC to local time
    current_age = utc_time + timezone_offset

    return humanize.naturaltime(current_age)


def output_option(function):
    """ click decorator for specifying output format. """
    function = click.option(
        "--output",
        "-o",
        type=click.Choice(OutputFormat),
        default=OutputFormat.table,
        help="The format to display output data in."
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
            # Skip empty colums for display
            if val is None or val == '':
                continue
            # Skip columns that are not in the display columns
            if endpoint and key not in DISPLAY_COLUMNS.get(endpoint):
                continue
            # Format values that are timestamps
            if 'added' in key or 'edited' in key:
                val = get_datetime_age(val)
            # rename the keys
            new_data[KEY_MAPS.get(key) or key.upper()] = val

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
    if output == OutputFormat.table:
        table(data, endpoint)
    elif output == OutputFormat.json:
        data = json.dumps(data, indent=4, sort_keys=True)
        if sys.stdout.isatty(): # TODO: use isatty() in the click.echo for color
            data = highlight(
                data,
                lexers.JsonLexer(),
                PYGMENTS_FORMATTER,
            )
        click.echo(data)
    elif output == OutputFormat.yaml:
        data = yaml.dump(data)
        if sys.stdout.isatty():
            data = highlight(
                data,
                lexers.YamlLexer(),
                PYGMENTS_FORMATTER,
            )
        click.echo(data)


def format_log(
    log: str,
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

    # Remove the TaskID from operator server log
    # 00:37:37.000 operator-serve I: Task:3-simplefunction1g-d1bf610e-6v4:#30 DONE 0.0s
    # becomes
    # 00:37:37.000 operator-serve I: #30 DONE 0.0s
    log = re.sub(r"Task:.*:", "", log)

    # Rename "operator-serve" to "build-log" so it's more meaningful to users
    container_name = container_name.replace("operator-serve", "build-log")

    # Remove IP addresses
    log = IP_ADDRESS_PATTERN.sub("", log)

    # Remove double spacing
    log = " ".join(log.split())

    # Format log
    formatted_log = (timestamp, f"{container_name} {verbosity}: {log}")
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
            format_log(log, container_name)
            for container_name, container in data.items()
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
