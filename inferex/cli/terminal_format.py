""" Formatting helpers for ERRORS / SUCCESS / LOG messages to be written to console """
import click


TAB_CHAR = "  "  # Taken from legacy term code, not all terminals represent
# \t as 4 spaces, they vary in [2, 4, 8]

SPINNER_COLOR = "cyan"

def error_style(err: str, indent: int = 0) -> str:
    """Format a string to display as an error

    Args:
        err: The error message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled error message ready to be displayed
    """
    style = click.style("❌ Error: ", fg="red")
    return TAB_CHAR * indent + style + err


def success_style(msg: str, indent: int = 0) -> str:
    """Format a string to display as success

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled error message ready to be displayed
    """
    style = click.style("✅ Success: ", fg="green")
    return TAB_CHAR * indent + style + msg


def info_style(msg: str, indent: int = 0) -> str:
    """Format a string to display as a normal message (no styling)

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled message ready to be displayed
    """
    styled_msg = click.style(msg, fg="reset")
    return TAB_CHAR * indent + styled_msg


def error(err: str, indent: int = 0) -> None:
    """Helper function to show error messages. Writes to stderr.

    Args:
        err: The message to display to the user
        indent: The number of tab indents for alignment
    """
    click.echo(error_style(err, indent), err=True)


def success(msg: str, indent: int = 0) -> None:
    """Helper function to show success messages.

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment
    """

    click.echo(success_style(msg, indent))


def info(msg: str, indent: int = 0) -> None:
    """Helper function to show info messages.

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment
    """
    click.echo(info_style(msg, indent))
