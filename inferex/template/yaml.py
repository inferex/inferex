""" Config template """


def default_project(project_name: str) -> str:
    """Return a default configuration YAML

    Args:
        project_name: The name of the users inferex project

    Returns:
        str: The boilerplate configuration YAML
    """

    return f"""
project:
  name: {project_name}

"""
