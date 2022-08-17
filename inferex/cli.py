""" Inferex CLI main command group & core commands. """
import sys
from typing import Optional
from datetime import datetime, timedelta, timezone

import click

from inferex import __version__
from inferex import Client
from inferex.utils import AliasedGroup
from inferex.io.termformat import info
from inferex.io.output import display_logs
from inferex.help.help_texts import TIME_HELP_TEXT
from inferex.utils import disable_user_prompts
from inferex.projects.cli import commands as project_commands
from inferex.deployments.cli import commands as deployment_commands
from inferex.deployments.cli import deployments
from inferex.endpoints.cli import commands as endpoint_commands
from inferex.io.git import get_commit_sha_and_date


# CLI
@click.command(cls=AliasedGroup, name="inferex")
@click.version_option(version=f"{__version__} {get_commit_sha_and_date()}")
def cli():
    """
    Inferex CLI is a tool that enables AI companies to rapidly deploy pipelines.
    Init, deploy, and manage your projects with Inferex.
    Invoke "inferex --help" for a list of commands.
    """


# Core commands
@cli.command()
@click.argument("path", type=click.Path(exists=True))
def init(path: str):
    """
    ✨ Initializes a new project.

    path: Full or relative path to a project folder.
    \f
    Args:
        path: Full or relative path to project folder.
    """
    client = Client()
    client.init(path)


@cli.command()
@click.option(
    "--username",
    help="Your Inferex username.",
    prompt="👤 Inferex Username",
    default=None
)
@click.password_option(
    help="Your Inferex password.",
    prompt="🔑 Inferex Password",
    hide_input=True,
    confirmation_prompt=False,
    default=None
)
@disable_user_prompts
def login(username: Optional[str], password: Optional[str], q: Optional[str]):  # pylint: disable=C0103, W0613
    """
    🔑 Fetch api key via username & password authentication.
    \f

    Args:
        username: Inferex account username.
        password: Inferex account password.
        q: -q flag to suppress user prompts.
    """
    # password passed in via stdin
    if password == "-":  # nosec
        password = sys.stdin.read().strip()

    if not username or not password:
        click.echo("Username or password not supplied, exiting.", err=True)
        sys.exit(1)

    # Create client and login
    client = Client()
    client.login(username, password)


@cli.command("deploy")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Uses a random SHA as the deployment ID to bypass duplicate constraints."
)
@click.option(
    "--token",
    default=None,
    help="Pass in a JWT token instead of reading from local cache."
)
@click.argument("path", default=".")
def deploy(force: bool, token: Optional[str], path: Optional[str]):
    """\b 🚀 Deploy a project.

    This command will bundle an application in [PATH] and submit it for processing.

    path: Full or relative path to a project folder.
    \f

    Args:
        force: Uses a random SHA as the deployment ID to bypass duplicate constraints.
        token: Pass a JWT token instead of reading from local cache.
        path: Full or relative path to a project folder.
    """
    client = Client()
    client.deploy(path, force, token)


@cli.command("logs")
@click.option(
    "--limit",
    default=1000,
    help="The total number of logs to gather across all streams."
)
@click.option("--earliest", default=None, help=TIME_HELP_TEXT)
@click.option("--latest", default=None)
@click.argument("git_sha")
def logs(
    limit: Optional[int],
    earliest: Optional[str],
    latest: Optional[str],
    git_sha: str,
):
    """\b
    📃 Get logs from Inferex deployments.
    E.g., 'inferex logs <git_sha>'

    git_sha: Git sha of the deployment to get logs from (required).
    \f

    Args:
        limit (int): The number of lines to return.
        earliest: How far back to look in time.
        latest: No more recent than this point in time.
        git_sha: Git sha of a deployment.
    """
    # Get operator client
    client = Client()

    # request params
    params = {
            "git_sha": git_sha,
            "limit": limit,
            "start": None,
            "end": None,
            }

    # Calculate time deltas
    for key, time_range in [("start", earliest), ("end", latest)]:
        if time_range is None:
            continue
        if time_range.endswith("s"):
            delta = timedelta(seconds=int(time_range.replace("s", "")))
        elif time_range.endswith("m"):
            delta = timedelta(minutes=int(time_range.replace("m", "")))
        elif time_range.endswith("h"):
            delta = timedelta(hours=int(time_range.replace("h", "")))
        elif time_range.endswith("d"):
            delta = timedelta(days=int(time_range.replace("d", "")))
        elif time_range.endswith("w"):
            delta = timedelta(weeks=int(time_range.replace("w", "")))
        else:
            info("Unsupported unit of time, using default range.")
            continue

        # use UTC offset
        dt = datetime.now() - datetime.now(timezone.utc).astimezone().utcoffset()  # pylint: disable=C0103
        dt = dt - delta  # pylint: disable=C0103
        params[key] = dt.isoformat()

    # Get endpoints
    response_data = client.get(
        "logs",
        params=params
    ).json()

    # check if any data was returned, and if not, inform the user about time ranges
    if not response_data:
        info("No logs were returned. Try increasing the time range, see "
             "'inferex logs --help' for information on options."
        )

    if "error" in response_data or "errors" in response_data:
        # Currently Loki returns a response with "error" as a key
        # In the future, we plan on putting error messages in one place,
        # keyed as "errors".
        info(f"Error with querying logs. {response_data}")
        sys.exit(1)

    display_logs(response_data)


@cli.command("reset")
def reset():
    """ ❌ Deletes the token.json file created at login."""
    client = Client()
    client.reset()


# Add subcommands to the "cli" group.
cli.add_command(project_commands)
cli.add_command(deployment_commands)
cli.add_command(deployments)
cli.add_command(endpoint_commands)


if __name__ == "__main__":
    cli()
