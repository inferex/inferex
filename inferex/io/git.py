""" Git repo helper functions """
import sys
import os
import random
import shutil
import string
import tempfile
from pathlib import Path
from datetime import datetime

import click
from dirhash import dirhash

try:
    import git
    from git import InvalidGitRepositoryError, GitCommandError
except ImportError:
    InvalidGitRepositoryError = ValueError
    GitCommandError = ValueError

from inferex.io.termformat import error, info


SHORT_SHA_LENGTH = 8

# TODO: same as client.py:40
IGNORED_PATTERNS = [
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".egg-info",
    ".vscode",
    "/dist",
]


def git_sha(target_dir: Path, randomize=False) -> str:
    """Get the current git project SHA

    If the given path (or anywhere in parent directories) is a git repo, then
    the current git commit SHA is returned

    Args:
        target_dir (Path): A path to the current project
        randomize (Bool): Add entropy to SHA to circumvent duplicate detection

    Returns:
        sha (str): A git SHA of the users repo
    """

    # Make it a Path object
    target_dir = Path(target_dir)

    # Make sure it exists
    if not target_dir.exists():
        error(f"{target_dir} does not exist.")
        sys.exit(1)

    # Empty dir raises error
    if not any(target_dir.iterdir()):
        error(f"{target_dir} is empty, please add files to it.")
        sys.exit(1)

    try:
        # Find a git repo in this directory
        # TODO: consider search_parent_directories=True
        project_repo = git.Repo(target_dir, search_parent_directories=False)

        # Create a temporary directory to clone the repo into
        with tempfile.NamedTemporaryFile() as temp_file:
            # Copy the git repo to the temporary directory
            shutil.copy(f"{project_repo.git_dir}/index", temp_file.name)
            os.environ["GIT_INDEX_FILE"] = temp_file.name

            # Add all files to the index
            # TODO: git fails if there are no commits
            # TODO: shouldn't this be the tempfile?
            git_repo = git.Git(target_dir)
            git_repo.execute(["git", "add", "--all"])

            # Get the SHA
            deployment_sha = git_repo.execute(
                ["git", "write-tree"]
            )[:SHORT_SHA_LENGTH]
    except (
        InvalidGitRepositoryError,  # InvalidGitRepositoryError
        ValueError,  # ValueError repo exists, but has no commits
        NameError,  # NameError git not installed
    ):
        click.echo("GitPython is not installed, please install it to use this feature.", err=True)
        # Compute the hash ourselves
        deployment_sha = dirhash(
            target_dir,
            "sha1",
            ignore=IGNORED_PATTERNS
        )[:SHORT_SHA_LENGTH]
        info(f"No git repository found, using generated SHA: {deployment_sha}.")

    if randomize:
        rand_string = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(3)
        )
        deployment_sha = f"{deployment_sha}-{rand_string}"

    return deployment_sha


def get_commit_sha_and_date():
    """
    Get the git sha and date and return a formatted string.

    Returns:
        version_and_date_string (str): a formatted string containing the first
            7 characters of git commit sha and its date.
    """
    import inferex
    PROJECT_ROOT = os.path.abspath(os.path.dirname(inferex.__file__))
    target_directory = Path(os.path.abspath(PROJECT_ROOT)).parent
    try:
        git_repo = git.Git(target_directory)
        timestamp = git_repo.log("-1", "--format=%at")
        timestamp = datetime.fromtimestamp(int(timestamp))
        date_str = timestamp.strftime("%Y-%m-%d")
        repo = git.Repo(target_directory)
        sha = repo.head.object.hexsha[:7]
        version_and_date_string = f"({sha}, {date_str})"
    except (InvalidGitRepositoryError, GitCommandError, NameError):
        # git is not installed
        return ""
    return version_and_date_string
