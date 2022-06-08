""" Main entry point for CLI application """

import traceback

from inferex import __app_name__, cli
from inferex.io.human import technical_support


def main():
    """Main entry point for application, this is the function that console_scripts will target
    and will be run when "inferex" is executed as a command from the CLI
    """
    try:
        cli.app(prog_name=__app_name__)
    except Exception as exc:  # pylint: disable=W0703
        print(
            "\nTraceback:\n"+ "\n".join(traceback.format_tb(exc.__traceback__)) +
            f"Unhandled exception - {exc}"
            f"{technical_support()}"
        )


if __name__ == "__main__":
    main()
