""" Top-level package for Inferex CLI """

__app_name__ = "inferex"
__version__ = "0.1.0"

import logging
from logging import NullHandler

from inferex.decorator.inferex import pipeline
from inferex.cli import cli

from .sdk.resources import deployments
from .sdk.resources.deployments import Deployment, deploy

from .sdk.resources import pipelines
from .sdk.resources.pipelines import Pipeline

from .sdk.resources import projects
from .sdk.resources.projects import Project

from .sdk.resources import logs
from .sdk.resources.logs import Log

from .sdk.http import api_session, init, login


__all__ = [
    "pipeline",
    "cli",

    "api_session",
    "init",
    "login",

    "Deployment",
    "deployments",
    "deploy",

    "Pipeline",
    "pipelines",

    "Log",
    "logs",

    "Project",
    "projects",
]

logging.getLogger(__name__).addHandler(NullHandler())
