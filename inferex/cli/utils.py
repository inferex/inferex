""" Reusable classes and decorators for Click commands. """
import sys

import click

from inferex.utils.io.termformat import error


class AliasedGroup(click.Group):
    """ Custom group for matching command prefixes. """
    # https://pocoo-click.readthedocs.io/en/latest/advanced/  # pylint: disable=R1710
    def get_command(self, ctx, cmd_name):
        return_value = click.Group.get_command(self, ctx, cmd_name)
        if return_value is not None:
            return return_value
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many command matches: {', '.join(sorted(matches))}. Try using one of these commands.")


def deactivate_prompts(ctx, _param, value):
    """ Prevents a Click command from raising user prompts. """
    if value == "noninteractive":
        prompt_disabled = False
        for cmd_param in ctx.command.params:
            if isinstance(cmd_param, click.Option) and cmd_param.prompt is not None:
                cmd_param.prompt = None
                prompt_disabled = True

        if prompt_disabled:
            click.echo("User prompts are disabled due to the DEBIAN_FRONTEND env var.")

    return value


def disable_user_prompts(function):
    """ Option decorator to disable user prompts for commands. """
    function = click.option(
        "-_",
        envvar="DEBIAN_FRONTEND",
        help="Disable all prompts.",
        flag_value=str,
        default=False,
        is_eager=True,
        expose_value=True,
        callback=deactivate_prompts,
        hidden=True
        )(function)
    return function


def fetch_and_handle_response(func, path, *args, **kwargs):
    """
    Calls the passed function with args and kwargs.
    Handles network exceptions, response, and displays output.

    Args:
        func(object): the function to be called.
        output_format(str): the format to output the data.
        path(str): the URL path to make a request to.
        *args: the args to pass to "func"
        **kargs: the kwargs to pass to "func"

    Returns:
        response_dict(dict): the response data from the request.
    """

    # request data from the api
    try:
        response = func(*args, **kwargs)
    except Exception as exc:
        error(str(exc))
        sys.exit()

    if "application/json" in response.headers.get('Content-Type'):
        content = response.json()
    else:
        content = response.content

    # non-200 response
    if not response.ok:
        error(
            f"""Non-200 response from /{path}.
                status_code: {response.status_code}
                response: {content}"""
        )
        sys.exit()

    # no json data is returned
    if "application/json" not in response.headers.get('Content-Type'):
        error(
            f"""No data returned for request to /{path}
                status_code: {response.status_code}
                response: {content}"""
        )
        sys.exit()

    response_dict = response.json()
    if not response_dict:
        # TODO: display an empty table as it implies this?
        click.echo(f"No results from query to /{path} with args {args}")
        sys.exit()

    return response_dict
