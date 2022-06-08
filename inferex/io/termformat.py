""" Formatting helpers for ERRORS / SUCCESS / LOG messages to be written to console """
import typer


TAB_CHAR = "  "  # Taken from legacy term code, not all terminals represent
# \t as 4 spaces, they vary in [2, 4, 8]


SPINNER_COLOR = "cyan"


def error_style(err: str, indent: int = 1) -> str:
    """Format a string to display as an error

    Args:
        err: The error message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled error message ready to be displayed
    """
    style = typer.style("❌ Error: ", fg=typer.colors.RED)
    return TAB_CHAR * indent + style + err


def success_style(msg: str, indent: int = 1) -> str:
    """Format a string to display as success

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled error message ready to be displayed
    """
    style = typer.style("✅ Success: ", fg=typer.colors.GREEN)
    return TAB_CHAR * indent + style + msg


def info_style(msg: str, indent: int = 1) -> str:
    """Format a string to display as a normal message (no styling)

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment

    Returns:
        str: The styled message ready to be displayed
    """
    styled_msg = typer.style(msg, fg=typer.colors.RESET)
    return TAB_CHAR * indent + styled_msg


def error(err: str, indent: int = 1) -> None:
    """Helper function to show error messages, less verbose than typer.echo(error_style)

    Args:
        err: The message to display to the user
        indent: The number of tab indents for alignment
    """
    typer.echo(error_style(err, indent))


def success(msg: str, indent: int = 1) -> None:
    """Helper function to show success messages, less verbose than typer.echo(success_style)

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment
    """

    typer.echo(success_style(msg, indent))


def info(msg: str, indent: int = 1) -> None:
    """Helper function to show info messages, less verbose than typer.echo(info_style)

    Args:
        msg: The message to display to the user
        indent: The number of tab indents for alignment
    """
    typer.echo(info_style(msg, indent))
