""" Git repo helper functions """
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import typer
import git
from git import InvalidGitRepositoryError
from inferex.io.termformat import info

SHORT_SHA_LENGTH = 8


def git_sha(target_dir: Path) -> str:
    """Get the current git project SHA

    If the given path (or anywhere in parent directories) is a git repo, then
    the current git commit SHA is returned, otherwise a random UUID is returned

    Args:
        target_dir (Path): A path to the current project

    Returns:
        sha (str): A git SHA of the users repo
    """

    try:
        project_repo = git.Repo(target_dir, search_parent_directories=False)
    except (InvalidGitRepositoryError, ValueError):
        # InvalidGitRepositoryError thrown when folder (or parents) is not a git repo
        # ValueError thrown when git repo exist, but has no commits
        #
        # We return a randomly generated SHA1
        # TODO: SHA the tar
        info("No git repo found, using random UUID.")
        sha = hashlib.sha1(str(uuid.uuid4()).encode("utf-8")).hexdigest()  # nosec
        return sha[:SHORT_SHA_LENGTH]

    with tempfile.NamedTemporaryFile() as temp_file:
        shutil.copy(f"{project_repo.git_dir}/index", temp_file.name)
        os.environ["GIT_INDEX_FILE"] = temp_file.name

        git_repo = git.Git(target_dir)
        git_repo.execute(["git", "add", "--all"])
        project_sha = git_repo.execute(["git", "write-tree"])
        return project_sha[:SHORT_SHA_LENGTH]
