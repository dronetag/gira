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
@click.option(
    "-f",
    "--format",
    "format",
    type=str,
    default="commit",
    help="Output format: commit, detail, markdown",
)
@click.argument("args", nargs=-1)
def main(config: str, ref: str, verbose: bool, format: str, args: list[str]) -> int:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    conf = config_parser.from_file(Path(config) if config else None)
    if not conf.dependencies:
        logger.error("No observed dependencies found in gira configuration file")
        return 1

    stream = sys.stdout
    precommit = len(args) > 0 and args[0] == ".git/COMMIT_EDITMSG"
    if precommit:
        commit_msg_file = args[0]
        logger.debug(f"Outputting to commit message file {commit_msg_file}")
        stream = Path(commit_msg_file).open("at", newline="\n")

    try:
        gira.gira(conf, format=format, stream=stream, ref=ref)
        return 0
    except Exception as e:
        logger.debug(e, stack_info=True)
        logger.error(str(e))
        return 1
    finally:
        if precommit:
            stream.close()


if __name__ == "__main__":
    sys.exit(main())
