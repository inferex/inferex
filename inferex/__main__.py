""" Main entry point for CLI application """

from inferex import __app_name__, cli
from inferex.help.human import technical_support


def main():
    """Main entry point for application, this is the function that console_scripts will target
    and will be run when "inferex" is executed as a command from the CLI
    """
    try:
        cli.app(prog_name=__app_name__)
    except Exception as exception:  # pylint: disable=W0703
        print(f"Unhandled exception - {exception}")
        print(technical_support())


if __name__ == "__main__":
    main()
