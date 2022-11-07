""" Inferex CLI main command group & core commands. """
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import click
import yaml

from inferex import __version__
from inferex.cli.commands.deployments import commands as deployment_commands
from inferex.cli.commands.deployments import deployments_list
from inferex.cli.commands.pipelines import commands as pipeline_commands
from inferex.cli.commands.pipelines import pipelines_list
from inferex.cli.commands.projects import commands as project_commands
from inferex.cli.commands.projects import projects_list
from inferex.cli.utils import (CustomGroup, disable_user_prompts,
                               fetch_and_handle_response)
from inferex.sdk.exceptions import DeployFailureError
from inferex.sdk.http import login
from inferex.sdk.resources import deployments, logs
from inferex.sdk.settings import settings
from inferex.cli.display import TIME_HELP_TEXT, display_logs
from inferex.cli.terminal_format import error, success
from inferex.common.project import DEFAULT_PROJECT


@click.command(cls=CustomGroup, name="inferex")
@click.version_option(version=__version__)
def cli():
    """
    Rapidly deploy and manage Inferex pipelines
    """


# Core commands
@cli.command()
@click.argument("project_path", default=".", type=click.Path(exists=True))
@click.option("--project-name", prompt="Enter Project name", help="Name of project")
@disable_user_prompts
def init(project_path: str, project_name: Optional[str], _: Optional[str]):
    """
    ✨  Initialize a new project

        PROJECT_PATH: full or relative path to a project directory.

    \f
    Args:
        path: Full or relative path to project directory.
    """
    path = Path(project_path)

    # Check if inferex.yaml already exists
    yaml_file = path / "inferex.yaml"
    if yaml_file.is_file():
        click.echo(f"inferex.yaml already exists in {path.absolute()}, exiting.")
        sys.exit(0)

    # Create inferex.yaml
    with open(yaml_file, "w", encoding="utf-8") as file:
        if project_name:
            yaml.dump({"project": {"name": project_name}, "scaling": {"replicas": 1}}, file)
        else:
            yaml.dump(DEFAULT_PROJECT, file)

    success(f"Project {project_name} initialized in {path.absolute()}")
    click.echo("📝 Edit the 'inferex.yaml' file to customize deployment parameters.")


@cli.command("login", context_settings=dict(allow_extra_args=True))
@click.option(
    "--username",
    help="Inferex username.",
    prompt="👤 Inferex Username",
    default=None,
)
@click.password_option(
    help="Inferex password.",
    prompt="🔑 Inferex Password",
    hide_input=True,
    confirmation_prompt=False,
    default=None
)
@disable_user_prompts
def cli_login(username: Optional[str], password: Optional[str], _: Optional[str]):
    """\b
    🔑  Log in to Inferex CLI
        \b
        Username and password may be set through environment variables or an .inferex file:
            INFEREX_USERNAME=myuser
            INFEREX_PASSWORD=mypassword

    \f
    Args:
        username: Inferex account username.
        password: Inferex account password.
    """
    # password passed in via stdin
    if password == "-":  # nosec
        password = sys.stdin.read().strip()

    if not username or not password:
        click.echo("Username or password not supplied. Env variables will be checked for credentials...")

    try:
        login(username=username, password=password)
    except Exception as exc:
        error(f"Login failed - {exc}")
        sys.exit()

    click.echo("🔑 Authenticated with provided credentials.")


@cli.command("deploy")
@click.option("--force",
    is_flag=True,
    default=False,
    help="Use a random SHA to bypass duplicate constraints."
)
@click.option(
    "--token",
    default=None,
    help="Pass in a JWT token instead of reading from local cache."
)
@click.option(
    "--detach",
    is_flag=True,
    default=False,
    help="Detached mode: push the deployment and do not stream logs.",
)
@click.argument("path", default=".")
def deploy(force: Optional[bool], token: Optional[str], detach: Optional[bool], path: str):
    """
    🚀  Deploy a project

        PATH: full or relative path of the project directory

    \f
    Args:
        force: Uses a random SHA as the deployment ID to bypass duplicate constraints.
        token: Pass a JWT token instead of reading from local cache.
        detach: Deploy without streaming logs.
        path: Full or relative path to a project directory.
    """
    click.echo("🐳 Preparing project...")
    start_time = time.time()
    try:
        response_or_stream = deployments.deploy(path, token, force=force, stream=not detach)
    except DeployFailureError as exc:
        error(f"Deploy failed: {exc}")
        sys.exit()
    except Exception as exc:
        error(str(exc))
        sys.exit()

    if detach and response_or_stream.ok:
        deploy_seconds = time.time() - start_time
        response_ms = str(response_or_stream.elapsed.microseconds / 1000).split(".")[0]
        click.echo(
            f"☁️  The project has been deployed for processing: {response_ms} ms\n"
            "It may take some time before pipelines are reachable."
        )
        click.echo(f"Pipeline deployed: ({deploy_seconds:.1f} s).")
    elif detach and not response_or_stream.ok:
        error(
            f"""Something went wrong with the deploy.
                Status code: {response_or_stream.status_code}
                Message: {response_or_stream.json()}"""
        )
    else:
        for log in response_or_stream:
            click.echo(log)


@cli.command("logs")
@click.option(
    "--limit",
    default=1000,
    help="The total number of logs to gather across all streams."
)
@click.option("--earliest", default=None, help=TIME_HELP_TEXT)
@click.option("--latest", default=None)
@click.argument("deployment_sha")
def logs_get(
    limit: Optional[int],
    earliest: Optional[str],
    latest: Optional[str],
    deployment_sha: str,
):
    """
    📃  Get logs of an Inferex deployment

    \f
    Args:
        limit (int): The number of lines to return.
        earliest: How far back to look in time.
        latest: No more recent than this point in time.
        deployment_sha: deployment_sha of a deployment.
    """
    # request params
    params = {
            "git_sha": deployment_sha,
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
            click.echo("Unsupported unit of time, using default range.")
            continue

        # use UTC offset
        dt = datetime.now() - datetime.now(timezone.utc).astimezone().utcoffset()  # pylint: disable=C0103
        dt = dt - delta  # pylint: disable=C0103
        params[key] = dt.isoformat()

    response_data = fetch_and_handle_response(
        func=logs.get,
        path="logs",
        **params
    )
    display_logs(response_data)


@cli.command("logout")
def logout():
    """ ❌  Log out from Inferex CLI """
    deleted_file_path = settings.delete_config()
    if deleted_file_path == 1:
        error("config.json not found. Please make sure you've run 'inferex login` first.")
    else:
        click.echo(f"Removed {deleted_file_path}")


# Add subcommands to the "cli" group.

cli.add_command(project_commands, command_group="Resource", priority=1)
cli.add_command(projects_list)
cli.add_command(deployment_commands, command_group="Resource", priority=2)
cli.add_command(deployments_list)
cli.add_command(pipeline_commands, command_group="Resource", priority=3)
cli.add_command(pipelines_list)


if __name__ == "__main__":
    cli()
