import argparse
import logging
import os
import sys
import traceback
from pathlib import Path

from . import AlrightException, gira, logger
from . import config as config_parser


def main() -> int:
    """Prepare gira to run with arguments from command line. Return exit code."""
    parser = argparse.ArgumentParser(description="Gira - Git Dependencies Analyzer")
    parser.add_argument(
        "-r",
        "--ref",
        type=str,
        help="Diff to specific commit hash/branch/tag. "
        "Otherwise staged/unstaged or last commit is used",
    )
    parser.add_argument("-c", "--config", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-f", "--format", type=str, default="commit", help="Output format: commit, detail, markdown"
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(sys.argv[1:])
    precommit = len(args.args) > 0 and args.args[0] == ".git/COMMIT_EDITMSG"
    stream = sys.stdout

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, stream=sys.stderr)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.debug(f"Arguments: {args}")
    try:
        conf = config_parser.from_file(Path(args.config).resolve() if args.config else None)
        if not conf.observe and not conf.submodules:
            logger.error("No observed dependencies found in gira configuration file")
            return 1

        if precommit:
            commit_msg_file = args.args[0]
            logger.debug(f"Outputting to commit message file {commit_msg_file}")
            stream = Path(commit_msg_file).open("at", newline="\n")

        gira.gira(conf, format=args.format, stream=stream, ref=args.ref)
        return 0
    except AlrightException as e:
        logger.info(e)
        return 0
    except Exception as e:
        logger.error(f"{e.__class__.__name__}: {e}")
        if args.verbose:
            traceback.print_exception(e, file=sys.stderr)
        return 1
    finally:
        if precommit:
            stream.close()


if __name__ == "__main__":
    if os.getenv("CI") is not None:
        print("Gira does not run in CI environments", file=sys.stderr)
        sys.exit(0)
    sys.exit(main())
