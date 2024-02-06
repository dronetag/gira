import argparse
import logging
import sys
from pathlib import Path

from . import config as config_parser
from . import gira, logger


def main() -> int:
    """Prepare gira to run with arguments from command line. Return exit code."""
    parser = argparse.ArgumentParser(description="Gira - Git Dependencies Analyzer")
    parser.add_argument("-r", "--ref", type=str)
    parser.add_argument("-c", "--config", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-f", "--format", type=str, default="commit", help="Output format: commit, detail, markdown"
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, stream=sys.stderr)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.debug(f"Arguments: {args}")
    conf = config_parser.from_file(Path(args.config) if args.config else None)
    if not conf.observe and not conf.submodules:
        logger.error("No observed dependencies found in gira configuration file")
        return 1

    stream = sys.stdout
    precommit = len(args.args) > 0 and args.args[0] == ".git/COMMIT_EDITMSG"
    if precommit:
        commit_msg_file = args.args[0]
        logger.debug(f"Outputting to commit message file {commit_msg_file}")
        stream = Path(commit_msg_file).open("at", newline="\n")

    try:
        gira.gira(conf, format=args.format, stream=stream, ref=args.ref)
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
