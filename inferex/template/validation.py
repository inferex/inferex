""" Validation and Exception code for inferex.yaml project files """


from pathlib import Path

import yaml
from cerberus import Validator

CONFIG_SCHEMA = {
    "compute": {
        "required": False,
        "type": "dict",
        "schema": {
            "gpu": {
                "required": False,
                "type": "dict",
                "schema": {
                    "type": {"required": True, "type": "string"},
                    "count": {"required": True, "type": "number", "min": 1, "max": 99},
                },
            },
            "cpu": {
                "required": False,
                "type": "dict",
                "schema": {
                    "type": {"required": True, "type": "string"},
                    "count": {"required": True, "type": "number", "min": 1, "max": 99},
                },
            },
        },
    },
    "project": {
        "required": True,
        "type": "dict",
        "schema": {"name": {"required": True, "type": "string"}},
    },
    "scaling": {
        "required": False,
        "type": "dict",
        "schema": {
            "replicas": {"required": True, "type": "number", "min": 1, "max": 10},
        },
    },
}


class ConfigInvalid(Exception):
    """We wrap various libraries exceptions in a more generalized
    ConfigInvalid exception, so that the calling code has only 1
    type to catch"""


def validate_project_file(cfg_file: Path):
    """Perform schema validation on the inferex.yaml config

    Args:
        cfg_file (Path): Filesystem path of inferex.yaml to validate

    Raises:
        ConfigInvalid: Throws a exception on any error, this exception is
                       designed to be end-user facing, with the target being the
                       project developer
    """

    with open(cfg_file, encoding="utf-8") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as ex:
            raise ConfigInvalid(ex) from ex

        validator = Validator(CONFIG_SCHEMA)

        if validator.validate(cfg) is False:
            raise ConfigInvalid(str(validator.errors))
