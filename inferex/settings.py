""" Configuration setting that alter CLI's behavior"""
import os


DEBIAN_FRONTEND = True if os.getenv("DEBIAN_FRONTEND") == 'noninteractive' else False  # pylint: disable=R1719
DEFAULT_DC_REGION = "ie"
INFEREX_TOKEN = os.getenv("INFEREX_TOKEN")
