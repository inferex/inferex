""" Reusable classes and decorators for Click commands. """
import sys
from gettext import gettext as _
from typing import Dict, List, Optional

import click
from click import Command, Context
from click.formatting import HelpFormatter

from inferex.cli.terminal_format import error


class CustomGroup(click.Group):
    """ Overrides default click group

    Differences:
        Auto-completes commands when possible.
        Reorders commands using priority parameter in command decorator.
            Default: alphabetical
            Example: @cli.command(priority=1)
        Adds custom command_groups using command_group parameter in command decorator.
            Example: @cli.command(command_group="resource")
    """

    def __init__(self, *args, **kwargs):
        """
        Example command_priority:
            {
                "Commands": {
                    "deploy": 1,
                    "init": 1,
                },
                "Resources": {
                    "deployment": 2,
                    "project": 1,
                }
            }
        """
        # storage for custom priority
        self.command_priority = {}
        super(CustomGroup, self).__init__(*args, **kwargs)

    def get_command(self, ctx: Context, command_name: str) -> Optional[Command]:
        """
        Given a context and a command name, returns Command object if it exists.

        Overriden to:
        Auto-competes commands by matching command prefixes.
        Fails with error message if there's too many command matches.

        https://pocoo-click.readthedocs.io/en/latest/advanced/  pylint: disable=R1710

        Args:
            ctx: CLI context information.
            command_name: Name of the command.

        Returns:
            Command or None with fail message
        """
        # if exact command exists return it
        command = click.Group.get_command(self, ctx, command_name)
        if command is not None:
            return command

        # else check for commands with matching prefix
        matches = [command for command in self.list_commands(ctx)
                   if command.startswith(command_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many command matches: {', '.join(sorted(matches))}. Try using one of these commands.")

    def get_col_spacing(self, commands: List[tuple], min_spacing: int=2) -> Dict:
        """ Returns correct column spacing for aligning help text

        Args:
            commands: List of command tuples (command_name: str, command: Command)
            min_spacing: minimum spacing between first (command name) and second (help text) column

        Returns:
            Returns dictionary with column spacing value for each command group.
            Example:
            {
                "Commands": 6,
                "Resources": 2
            }
        """
        col_spacing = {}

        # get longest command name for each group of commands
        for command_group in commands:
            name_length = max(len(name[0]) for name in commands[command_group])
            col_spacing[command_group] = name_length

        # get longes command name and set spacing based off that
        max_name_length = max(col_spacing[command_group] for command_group in col_spacing)
        for command_group in col_spacing:
            col_spacing[command_group] = max_name_length - col_spacing[command_group] + min_spacing
        return col_spacing

    def format_commands_extra(self, ctx: Context, formatter: HelpFormatter) -> None:
        """Format the commands using command groups and priorities

        Overrides the default format_command

        Args:
            ctx: CLI context information
            formatter (HelpFormatter): _description_
        """
        commands = {}
        # sort command group
        # curerently: reverse alphabetically so that Commands is last
        for command_group in sorted(self.command_priority.keys(), reverse=True):
            command_list = []

            # sort commands under each command group by priority value first, then alphabetically
            for command_name in sorted(self.command_priority[command_group].keys(),
                                  key=lambda command_name: (
                                      self.command_priority[command_group][command_name],
                                      command_name)):
                command = super(CustomGroup, self).get_command(ctx, command_name)

                # exclude commands that don't exist or are hidden
                if command is None or command.hidden:
                    continue
                command_list.append((command_name, command))
            commands[command_group] = command_list

        if not commands:
            return

        col_spacing = self.get_col_spacing(commands)

        for command_group in commands:
            if commands[command_group]:
                # get the command and help texts
                rows = []
                for command_name, command in commands[command_group]:
                    help = command.get_short_help_str()
                    rows.append((command_name, help))

                # write the command group help text
                if rows:
                    with formatter.section(_(command_group)):
                        formatter.write_dl(rows, col_spacing=col_spacing[command_group])

    def get_help(self, ctx: Context) -> str:
        """Helper method to get formatted help page for the current context and command.
        Overrides the default command format to support command groups and priorities.

        Args:
            ctx: CLI context information

        Returns:
            help text
        """
        # override how the "Commands:"" section is displayed
        self.format_commands = self.format_commands_extra

        # keep the rest the same
        return super(CustomGroup, self).get_help(ctx)

    def update_command_priority(
        self,
        priority: int,
        command_group: str,
        command_name: str
    ) -> None:
        """Updates command priority with command_group and priority information

        Args:
            priority: Order in which commands should be displayed in help text
            command_group: Command group that the command belongs to
            command_name: Name of the command.

        Returns:
            None
        """
        group_dict = self.command_priority.get(command_group, {})
        group_dict[command_name] = priority
        self.command_priority[command_group] = group_dict

    def add_command(self, command: Command, name: str = None, **kwargs) -> None:
        """Registers command to the group.

        Args:
            command: Command to add.
            name: Name to override command with.
            kwargs: Priority and/or command_group if specified.

        Raises:
            TypeError: When no name is specified.
        """
        super(CustomGroup, self).add_command(command, name)

        # store the command group and priority of the command
        name = name or command.name
        priority = kwargs.pop('priority', 1)
        command_group = kwargs.pop('command_group', "Commands")
        self.update_command_priority(priority, command_group, name)

    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except captures a command_group
        and priority for listing command names in help.
        """
        priority = kwargs.pop('priority', 1)
        command_group = kwargs.pop('command_group', "Commands")

        def decorator(f):
            command = super(CustomGroup, self).command(*args, **kwargs)(f)
            self.update_command_priority(priority, command_group, command.name)
            return command

        return decorator


def deactivate_prompts(ctx, _param, value):
    """ Prevents a Click command from raising user prompts. """
    if value == "noninteractive":
        prompt_disabled = False
        for command_param in ctx.command.params:
            if isinstance(command_param, click.Option) and command_param.prompt is not None:
                command_param.prompt = None
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


def fetch_and_handle_response(func, path, exit_on_error=True, *args, **kwargs):
    """
    Calls the passed function with args and kwargs.
    Handles network exceptions, response, and displays output.

    Args:
        func(object): the function to be called.
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
        if exit_on_error:
            error(str(exc))
            sys.exit()
        raise

    if "application/json" in response.headers.get('Content-Type', {}):
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
    if "application/json" not in response.headers.get('Content-Type', {}):
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
