""" Reusable classes and decorators for Click commands. """
import click


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
        for cmd_param in ctx.command.params:
            if isinstance(cmd_param, click.Option) and cmd_param.prompt is not None:
                cmd_param.prompt = None

    return value


def disable_user_prompts(function):
    """ Option decorator to disable user prompts for commands. """
    function = click.option(
        "-q",
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
