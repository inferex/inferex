"""
    Functions related to IO.
"""
from inferex.utils.io.git import git_sha, SHORT_SHA_LENGTH
from inferex.utils.io.termformat import (
    error_style,
    success_style,
    info_style,
    error,
    success,
    info,
)
from inferex.utils.io.output import display_logs, TIME_HELP_TEXT
from inferex.utils.io.git import get_commit_sha_and_date
from inferex.utils.io.utils import get_project_config, default_project, ConfigSchemaException
# TODO: clean this up.

__all__ = [
    'git_sha',
    'SHORT_SHA_LENGTH',
    'error_style',
    'success_style',
    'info_style',
    'error',
    'success',
    'info',
    'get_project_config',
    'default_project',
    'ConfigSchemaException',
]
