import logging
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional, TypeVar

import click
import pygit2

from . import changes, core, dependencies, logger

T = TypeVar("T")


def _first(g) -> Optional[T]:
    for item in g:
        if item:
            return item
    return None


def _first_that(f: Callable[[T], bool], g: Iterable[T]) -> Optional[T]:
    for item in g:
        if f(item):
            return item
    return None


def _unwrap(o: Optional[T]) -> T:
    if o is None:
        raise ValueError("Optional value is None")
    return o


@click.command()
@click.option("-r", "--ref", "ref", type=str)
@click.option("-c", "--config", "config", type=str)
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True)
def main(config=None, ref=None, verbose=False) -> int:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)

    observed_dependencies = dependencies.from_file(Path(config) if config else None)
    logger.debug(f"Observed dependencies: {observed_dependencies}")

    # Diff current repository using firstly the revision if specified, then the staged
    # changes and then unstaged changes. We use diffs with 3 context lines that are necessary
    # for example for poetry.lock that has records spread over multiple lines
    repository = pygit2.Repository(".")
    diffs: pygit2.Diff = (
        repository.diff(a=ref, context_lines=3)
        if ref
        else _unwrap(
            _first_that(
                lambda diff: len(diff) > 0,
                map(
                    lambda kwargs: repository.diff(**kwargs),  # use map to lazy-evaluate the diffs
                    (
                        dict(a="HEAD", cached=True, context_lines=3),  # git diff --cached
                        dict(cached=False, context_lines=3),  # git diff
                        dict(a="HEAD^", context_lines=3),  # git diff HEAD^
                    ),
                ),
            )
        )
    )

    # extract changes from diffs of locks or other dependency specifying files
    # it modifies inplace the dependencies passed to it as argument
    upgrades: list[core.Upgrade] = []
    for diff in diffs:
        logger.debug(f"Changed file: {diff.delta.new_file.path}")
        if changes.extractable(diff):
            upgrades.extend(changes.extract(observed_dependencies, diff))

    logger.debug(f"Observed upgrades: {upgrades}")
    # commit_logs = commits.from(changes)

    print("dummy123: 1.0.0 => 1.1.0")
    print("JIRA-123: <blabla>")
    print("JIRA-543: <xyz>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
