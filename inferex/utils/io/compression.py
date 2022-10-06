import os
from pathlib import Path
import tarfile
from typing import List

from inferex.utils.io.logs import get_logger


logger = get_logger(__name__)

IGNORE_FILE_NODES = [
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".egg-info",
    ".vscode",
    "dist",
]

def get_ixignore_filenodes(target_dir: Path) -> List[str]:
    """
    Check .ixignore in the target path for files.
    Return a list of filenames.

    Args:
        target_dir(Path): the project folder to check for a .ixignore file.

    Returns:
        ignore_list(list): a list of filenames to ignore.
    """
    ixignore_file = target_dir / ".ixignore"
    ignore_list = ['.ixignore', ]
    if not ixignore_file.exists():
        logger.warning(f"{ixignore_file} does not exist.")
        return ignore_list

    with open(ixignore_file, "r", encoding="utf-8") as f:
        while (line := f.readline().rstrip()):
            ignore_list.append(line)

    return ignore_list


def gather_file_paths(target_dir: Path) -> List[Path]:
    """
    Recurse target directory and create a list of file paths.
    Ignore certain filesystem nodes based on IGNORE_FILE_NODES
    and .ixignore file, if it exists.

    Args:
        target_dir(Path): Target directory to walk.

    Returns:
        file_paths(list): A list of file Path objects.
    """
    file_paths = []
    ixignore_nodes = get_ixignore_filenodes(target_dir)
    ignore_nodes = IGNORE_FILE_NODES + ixignore_nodes
    for root, dirs, files in os.walk(target_dir, topdown=True):
        skipped_dirs = list(set(dirs).intersection(set(ignore_nodes)))
        # log skipped dirs
        for skip_dir in skipped_dirs:
            logger.info(f"Ignoring directory: {skip_dir}")

        # filter out ignored directory names
        dirs[:] = [d for d in dirs if d not in ignore_nodes]
        for file in files:
            file_path = Path(root) / file
            file_or_dir_name = file_path.absolute().name
            # log ignored files
            if any(ignore_node in file_or_dir_name for ignore_node in ignore_nodes):
                logger.info(f"Ignoring file: {file_path}")
                continue
            file_paths.append(file_path)

    return file_paths

def make_archive(archive_path: Path, target_dir: Path) -> int:
    """Compress a bundle of the users project into a tar.xz archive

    Args:
        tar_path (Path): The path to the tar.xz archive
        target_dir (Path): The path to the users Inferex project folder,

    Returns:
        bundle_size(int): The size of the archive.
    """
    # Create a tar.xz archive
    # See: https://github.com/python/cpython/blob/main/Lib/tarfile.py#L1744
    # TODO: detect if LZMA is supported
    bundle_size = 0
    try:
        tar = tarfile.open(archive_path, "w:xz")  # pylint: disable=consider-using-with
        file_paths = gather_file_paths(target_dir)
        for file_path in file_paths:
            # Get size and relative path
            bundle_size += file_path.stat().st_size
            relative_path = file_path.relative_to(target_dir)
            # Add the file to the tar archive
            tar.add(file_path, arcname=relative_path)

    except (ValueError, tarfile.CompressionError, tarfile.ReadError) as exc:
        logger.error(f"Error while compressing {target_dir} - {exc}")

    finally:
        tar.close()

    return bundle_size
