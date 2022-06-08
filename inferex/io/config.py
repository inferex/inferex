""" Helpers to read and write the config to the filesystem """
from pathlib import Path
import typer

from inferex.io.termformat import info


def get_config_file_path(app_name: str, filename: str) -> Path:
    """Get a Path object for the given filename within the .config/app_name directory

    Args:
        app_name: The CLI application name ("inferex")
        filename: The name of the config file to fetch

    Returns:
        fs_path (Path): The full path on the filesystem where the file is stored
    """
    app_dir = typer.get_app_dir(app_name)
    fs_path = Path(app_dir) / filename

    return fs_path


def delete_config_file(fullpath: Path) -> None:
    """Deletes a file from the system config folder.

    Args:
        fullpath: The full path to the file to delete on the filesystem
    """
    if fullpath.exists:
        fullpath.unlink()
        info(f"Deleted {fullpath}")
