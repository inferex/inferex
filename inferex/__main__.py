""" Main entry point for CLI application """

import traceback

from inferex import __app_name__
from inferex import cli


def main():
    """Main entry point for application, this is the function that console_scripts will target
    and will be run when "inferex" is executed as a command from the CLI
    """
    try:
        # cli.app(prog_name=__app_name__)
        cli(prog_name=__app_name__)
    except Exception as exc:  # pylint: disable=W0703
        print( # TODO: format traceback to show relevant lines
            "\nTraceback:\n"+"\n".join(traceback.format_tb(exc.__traceback__)) +
            f"Unhandled exception - {exc}"
            "\n\nNeed assistance? \033[1mSpeak to an engineer!\033[0m "
            "https://calendly.com/inferex\n\n"
        )


if __name__ == "__main__":
    main()
