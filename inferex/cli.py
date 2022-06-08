"""
    Inferex CLI

    Usage: inferex [SUBAPP] [command]

    Where [SUBAPP] is:
        - login     :   Attempt API login to validate credentials and generate an access token
        - inference :   Module to handle user project lifecycle and execution
        - configure :   Set platform login details (TODO: Auth via API Key only?)
        - deploy    :   Deploy a project


    Examples:

        inferex login           Authenticate to server
        inferex deploy          Deploy a project to Inferex infrastructure
"""
import sys
from typing import Optional

import typer

from inferex import __version__, __app_name__
from inferex.io.config import delete_config_file, get_config_file_path
from inferex.io.git import git_sha
from inferex.io.termformat import error, info, success
from inferex.io.token import jwt_cache_path
from inferex.io.utils import normalize_project_dir, valid_inferex_project
from inferex.subapp.login import login_app
from inferex.subapp.deploy import run_deploy
from inferex.subapp.logs import logs_app
from inferex.subapp.get import get_app
from inferex.subapp.delete import delete_app
from inferex.template.validation import ConfigInvalid
from inferex.template.yaml import default_project


app = typer.Typer()
app._add_completion = False  # pylint: disable=protected-access
app.add_typer(login_app, name="login")
app.add_typer(get_app, name="get")
app.add_typer(delete_app, name="delete")
app.add_typer(logs_app, name="logs")


def init(path: str, project_name: str):
    """Creates a new project in the target folder.

    Args:
        path: The path to the users project directory
        project_name: The name of the users project

    Raises:
        Exit: Typer exit if path/target_dir is not found.
    """
    target_dir = normalize_project_dir(path)

    if not target_dir.is_dir():
        error(f"{target_dir.absolute()} is not a directory")
        raise typer.Exit(code=1)

    if project_name is None:
        project_name = typer.prompt("Project name")

    yaml_file = target_dir / "inferex.yaml"
    if yaml_file.is_file():
        info(f"{yaml_file} already exists.")
        raise typer.Exit()

    with open(yaml_file, "w", encoding="UTF-8") as project_file:
        project_file.write(default_project(project_name))

    success(f"Project initialized at {target_dir.absolute()}.\n")
    info("📝 Edit the 'inferex.yaml' file to customize deployment parameters.\n")


@app.command("reset", help="❌ Deletes files created at login")
def reset(
    filename: Optional[str] = typer.Argument(
        None, help="(optional) filename to delete (e.g., token.json)"
    )
):
    """By default deletes the token.json file created at login.

    Args:
        filename: The file name to be deleted [optional]

    """
    if filename is not None:
        fullpath = get_config_file_path(__app_name__, filename)
        delete_config_file(fullpath)
    else:
        delete_config_file(jwt_cache_path(__app_name__))


@app.command("deploy", help="🚀 Deploy a project.")
def deploy(
    path: Optional[str] = typer.Argument(
        ".", help="Full or relative path to project folder."
    ),
):
    """This will bundle an application and submit it for processing

    Args:
        path: The filesystem path to the project directory root, containing an inferex.yaml

    Raises:
        Exit: Used to signal to typer framework that the main application thread
              should terminate, and return <int> to the OS
    """

    target_dir = normalize_project_dir(path)
    if not (target_dir / "inferex.yaml").is_file():
        info(f"inferex.yaml file was not found, writing one to {target_dir}")
        init(target_dir, target_dir.resolve().name)

    try:
        valid_inferex_project(target_dir)
    except ConfigInvalid as inv_cfg:
        error(f"Configuration error for file {target_dir}/inferex.yaml, {inv_cfg}\n")
        raise typer.Exit(1)

    sha = git_sha(target_dir)
    run_deploy(target_dir, git_sha=sha)


def version_callback(value: bool):
    """Eager function to print the version info and terminate

    Args:
        value: Supplied by typer in callback

    Raises:
        Exit: Typer exit exception to terminate app
    """
    if value:
        typer.echo(f"inferex v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    _version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Display version number.",
    ),
) -> None:
    """Init, deploy, and manage your projects with Inferex."""
    # 'inferex' by itself was invoked.
    if len(sys.argv) == 1:
        typer.echo("Enter 'inferex --help' for a list of commands.")
        raise typer.Exit()
