# pylint: disable=C0326
""" Base models to use with resource classes. """
from typing import Optional
from pathlib import Path

from pydantic import BaseModel


class ProjectBase(BaseModel):
    """ Defines 'project' data structure. """

    # present client-side
    name:                   str

    # returned by API
    added_at:               Optional[str]
    edited_at:              Optional[str]
    project_status:         Optional[str]
    terminated_at:          Optional[str]


class DeploymentBase(BaseModel):
    """ Defines 'deployment' data structure. """

    # present client-side
    git_sha:                Optional[str]
    path:                   Optional[Path]
    token:                  Optional[str]
    force:                  Optional[bool]  = False

    # returned by API
    version:                Optional[str]
    deployment_status:      Optional[str]
    deployment_timestamp:   Optional[str]
    deployment_url:         Optional[str]
    respository_url:        Optional[str]
    added_at:               Optional[str]  # TODO: Convert to native datetime?
    edited_at:              Optional[str]
    project_name:           Optional[str]


class PipelineBase(BaseModel):
    """ Defines 'pipeline' data structure."""
    git_sha:                Optional[str]
    project_name:           Optional[str]
    url:                    Optional[str]
    deployment_status:      Optional[str]
    added_at:               Optional[str]
    deployment_url:         Optional[str]
    version:                Optional[str]
    is_async:               Optional[str]


class LogBase(BaseModel):
    """ Defines 'logs' data strucutre. """
    # present client-side
    git_sha:                Optional[str]

    # returned by API
    data:                   Optional[dict]
