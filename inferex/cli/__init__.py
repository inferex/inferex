""" Inferex CLI main command group & core commands. """
import sys
import time
from typing import Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click
import yaml

from inferex import __version__
from inferex.sdk.resources import deployment, log
from inferex.sdk.http import login
from inferex.cli.utils import AliasedGroup, fetch_and_handle_response
from inferex.utils.io import error, success, default_project, display_logs, TIME_HELP_TEXT, get_commit_sha_and_date
from inferex.cli.commands.projects import commands as project_commands, projects
from inferex.cli.commands.deployments import commands as deployment_commands, deployments
from inferex.cli.commands.pipelines import pipelines
from inferex.cli.utils import disable_user_prompts
from inferex.sdk.settings import settings
from inferex.sdk.exceptions import DeployFailureError
from inferex.utils.io.scanning import RequirementsValidationException


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
@click.argument("project_path", default=".", type=click.Path(exists=True))
@click.option("--project-name", prompt="Enter Project name")
@disable_user_prompts
def init(project_path: str, project_name: Optional[str], _: Optional[str]):
    """
    ✨  Initializes a new project. Nondestructive.

        project_path: Full or relative path to a project folder.

    \f
    Args:
        path: Full or relative path to project folder.
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
            yaml.dump(default_project, file)

    success(f"Project {project_name} initialized in {path.absolute()}")
    click.echo("📝 Edit the 'inferex.yaml' file to customize deployment parameters.")


@cli.command("login", context_settings=dict(allow_extra_args=True))
@click.option(
    "--username",
    help="Your Inferex username.",
    prompt="👤 Inferex Username",
    default=None,
)
@click.password_option(
    help="Your Inferex password.",
    prompt="🔑 Inferex Password",
    hide_input=True,
    confirmation_prompt=False,
    default=None
)
@disable_user_prompts
def cli_login(username: Optional[str], password: Optional[str], _: Optional[str]):
    """\b
    🔑  Fetch API key via username & password authentication.
        \b
        Username and password can be read from environment variables or set in an .inferex file:
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
    help="Uses a random SHA as the deployment ID to bypass duplicate constraints."
)
@click.option(
    "--token",
    default=None,
    help="Pass in a JWT token instead of reading from local cache."
)
@click.option(
    "--stream",
    is_flag=True,
    default=True,
    help="Runs deployment in the foreground and streams logs.",
    show_default=True
)
@click.argument("path", default=".")
def deploy(force: Optional[bool], token: Optional[str], path: str, stream: Optional[bool]):
    """
    🚀  Deploy a project.

        This command will bundle an application in [PATH] and submit it for processing.

        path: Full or relative path to a project folder.

    \f
    Args:
        force: Uses a random SHA as the deployment ID to bypass duplicate constraints.
        token: Pass a JWT token instead of reading from local cache.
        stream: Runs deployment in the background
        path: Full or relative path to a project folder.
    """
    click.echo("🐳 Preparing project...")
    start_time = time.time()
    try:
        response_or_stream = deployment.deploy(path, token, force=force, stream=stream)
    except DeployFailureError as exc:
        error(f"Deploy failed: {exc}")
        sys.exit()
    except RequirementsValidationException as exc:
        click.echo(f"Dependency issue with project - {exc}")
        sys.exit()
    except Exception as exc:
        error(str(exc))
        sys.exit()

    deploy_seconds = time.time() - start_time
    if stream:
        for log in response_or_stream:
            click.echo(log)
    elif response_or_stream.ok:
        response_ms = str(response_or_stream.elapsed.microseconds / 1000).split(".")[0]
        click.echo(
            f"☁️  The project has been deployed for processing: {response_ms} ms\n"
            "It may take some time before pipelines are reachable."
        )
        success(f"Pipeline deployed: ({deploy_seconds:.1f} s).")
    else:
        error(
            f"""Something went wrong with the deploy.
                Status code: {response_or_stream.status_code}
                Message: {response_or_stream.json()}"""
        )


@cli.command("logs")
@click.option(
    "--limit",
    default=1000,
    help="The total number of logs to gather across all streams."
)
@click.option("--earliest", default=None, help=TIME_HELP_TEXT)
@click.option("--latest", default=None)
@click.argument("deployment_git_sha")
def logs(
    limit: Optional[int],
    earliest: Optional[str],
    latest: Optional[str],
    deployment_git_sha: str,
):
    """
    📃  Get logs from Inferex deployments.

    \f
    Args:
        limit (int): The number of lines to return.
        earliest: How far back to look in time.
        latest: No more recent than this point in time.
        git_sha: Git sha of a deployment.
    """
    # request params
    params = {
            "git_sha": deployment_git_sha,
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

    response = log.get(**params)
    if "error" in response.json():
        error(
            f"""Something went wrong with the request.
                Status code: {response.status_code}
                Message: {response.json()}"""
        )
        sys.exit()

    response_data = fetch_and_handle_response(log.get, "logs", **params)
    display_logs(response_data)


@cli.command("reset")
def reset():
    """ ❌  Removes the config.json file created at login. """
    deleted_file_path = settings.delete_config()
    if deleted_file_path == 1:
        error("config.json not found. Please make sure you've run 'inferex login` first.")
    else:
        click.echo(f"Removed {deleted_file_path}")


# Add subcommands to the "cli" group.
cli.add_command(project_commands)
cli.add_command(projects)
cli.add_command(deployment_commands)
cli.add_command(deployments)
cli.add_command(pipelines)


if __name__ == "__main__":
    cli()
