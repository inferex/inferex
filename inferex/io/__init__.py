"""
    All operations pertaining to Inferex CLI functionality.
"""
from inferex.io.git import git_sha
from inferex.io.termformat import (
    error_style,
    success_style,
    info_style,
    error,
    success,
    info,
)
from inferex.io.utils import get_project_config

__all__ = [
    'git_sha',
    'error_style',
    'success_style',
    'info_style',
    'error',
    'success',
    'info',
    'get_project_config',
]
