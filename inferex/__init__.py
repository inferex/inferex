""" Top-level package for Inferex CLI """

__app_name__ = "inferex"
__version__ = "0.0.8"

import logging
from logging import NullHandler

from inferex.decorator.inferex import pipeline
from inferex.cli import cli

from .sdk.resources import deployment
from .sdk.resources.deployment import Deployment, deploy

from .sdk.resources import pipeline
from .sdk.resources.pipeline import Pipeline

from .sdk.resources import project
from .sdk.resources.project import Project

from .sdk.resources import log
from .sdk.resources.log import Log

from .sdk.http import api_session, init, login


__all__ = [
    "pipeline",
    "cli",

    "api_session",
    "init",
    "login",

    "Deployment",
    "deployment",
    "deploy",

    "Pipeline",
    "pipeline",

    "Log",
    "log",

    "Project",
    "project",
]

logging.getLogger(__name__).addHandler(NullHandler())
