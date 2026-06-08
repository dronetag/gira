import logging

from .__version__ import version as __version__

logger = logging.getLogger("gira")


class AlrightException(Exception):
    pass


__all__ = ["__version__", "AlrightException", "logger"]
