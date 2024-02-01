import logging
import sys
from pathlib import Path

import click

from . import config as config_parser
from . import gira, logger


@click.command()
@click.option("-r", "--ref", "ref", type=str)
@click.option("-c", "--config", "config", type=str)
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True)
@click.argument("files", nargs=-1)
def main(config=None, ref=None, verbose=False, files: list[str] = []) -> int:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)

    config = config_parser.from_file(Path(config) if config else None)
    if not config.dependencies:
        logger.error("No observed dependencies found in gira configuration file")
        return 1

    try:
        gira.gira(config, ref, files)
        return 0
    except Exception as e:
        logger.debug(e, stack_info=True)
        logger.error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
