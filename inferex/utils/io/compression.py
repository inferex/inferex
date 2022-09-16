from pathlib import Path
import tarfile

from inferex.utils.io.logs import get_logger


logger = get_logger(__name__)

IGNORED_PATTERNS = [
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".egg-info",
    ".vscode",
    "/dist",
]

def make_archive(archive_path: Path, target_dir: Path):
    """Compress a bundle of the users project into a tar.xz archive

    Args:
        tar_path (Path): The path to the tar.xz archive
        target_dir (Path): The path to the users Inferex project folder,

    Returns:
        bundle_size: The size of the archive.
    """
    # Create a tar.xz archive
    # See: https://github.com/python/cpython/blob/main/Lib/tarfile.py#L1744
    # TODO: detect if LZMA is supported
    # Track the size of the bundle
    bundle_size = 0

    try:

        tar = tarfile.open(archive_path, "w:xz")  # pylint: disable=consider-using-with

        for file_path in Path(target_dir).glob('**/*'):

            # Ignore bad files or directories
            file_path_str = str(file_path)
            if any(pattern in file_path_str for pattern in IGNORED_PATTERNS):
                # TODO: if very verbose, list files that are added / ignored. TODO: use .ixignore
                continue

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
