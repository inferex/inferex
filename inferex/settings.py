""" Configuration setting that alter CLI's behavior"""
import os


DEBIAN_FRONTEND = os.getenv("DEBIAN_FRONTEND") == "noninteractive"
DEFAULT_DC_REGION = "ie"
INFEREX_TOKEN = os.getenv("INFEREX_TOKEN")
