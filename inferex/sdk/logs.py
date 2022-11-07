import os
import logging


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(logger_name: str):
    """ Setup and return a logger instance. """
    logger = logging.getLogger(logger_name)
    development_environment = os.getenv("IX_DEBUG")
    if development_environment:
        handler = logging.StreamHandler()
        log_format = logging.Formatter(LOG_FORMAT, TIME_FORMAT)
        handler.setFormatter(log_format)
        logger.addHandler(handler)
    verbosity_level = logging.DEBUG if development_environment else logging.WARNING
    logger.setLevel(verbosity_level)
    return logger
