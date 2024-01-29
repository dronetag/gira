import re
from pathlib import Path
from typing import Generator, Iterable

import pygit2

from . import logger
from .core import Change, Dependencies, Upgrade

extractable_filenames = ("pyproject.toml", "package.lock", "poetry.lock")


def extractable(diff: pygit2.Diff) -> bool:
    """Extract changes in observed dependencies from dependency/lock files diffs"""
    return (
        diff.delta.new_file
        and diff.delta.old_file
        and diff.delta.new_file.path == diff.delta.old_file.path
        and Path(diff.delta.new_file.path).name in extractable_filenames
    )


def extract(dependencies: Dependencies, diff: pygit2.Diff) -> Iterable[Upgrade]:
    if not extractable(diff):
        return []

    path = Path(diff.delta.new_file.path)
    logger.debug("Extracting changes from %s", path)
    deps = {dep.name for dep in dependencies}
    upgrades: dict[str, Upgrade] = {}

    def apply_changes(changes: Iterable[Change]):
        for change in changes:
            if change.name not in deps:
                continue
            if change.name not in upgrades:
                upgrades[change.name] = Upgrade(name=change.name)
            if change.old:
                upgrades[change.name].old_version = change.version
            else:
                upgrades[change.name].new_version = change.version

    if path.name == "pyproject.toml":
        if dependencies.filetype == "pytoml":
            apply_changes(extract_pytoml(diff.hunks))
        if dependencies.filetype == "pytoml-poetry":
            apply_changes(extract_pytoml_poetry(diff.hunks))
    if path.name == "package.lock":
        apply_changes(extract_package_lock(diff.hunks))
    if path.name == "poetry.lock":
        apply_changes(extract_poetry_lock(diff.hunks))

    return upgrades.values()


def extract_pytoml(hunks: Iterable[pygit2.DiffHunk]) -> Generator[Change, None, None]:
    """Parse standart pytoml dependencies definition

    Example:
        [project]
        ...
        dependencies = [
            "pygit2==1.13.3; os_name != 'nt'",
            "django>2.1; os_name != 'nt'",
        ]
    """
    dep_re = re.compile(r"(\w+)\s*==([0-9]+\.[0-9]+[0-9a-zA-Z\.\-]*)")
    for hunk in hunks:
        for line in hunk.lines:
            if line.origin in ("+", "-") and "==" in line.content:
                match = dep_re.search(line.content)
                if match and len(match.groups()) >= 2:
                    yield Change(
                        name=match.group(1), version=match.group(2), old=(line.origin == "-")
                    )


def extract_package_lock(diff: pygit2.Diff) -> Generator[Change, None, None]:
    raise NotImplementedError()
    return []


def extract_pytoml_poetry(hunks: Iterable[pygit2.DiffHunk]) -> Generator[Change, None, None]:
    """The developer chould decide not to version poetry.lock so we need to parse pyproject.toml

    Example:
        [tool.poetry.dependencies]
        python = "^3.8"
        click = "*"
        pymavlink = "^2.4.20"
        ruff = {version="*", optional=true}
    """
    name_re = re.compile(r"^\s*(\w+)\s*=")
    version_re = re.compile(r"""["']([0-9]+\.[0-9]+[^"']*)""")
    for hunk in hunks:
        for line in hunk.lines:
            if line.origin in ("+", "-"):
                name_match = name_re.search(line.content)
                if name_match is None:
                    continue
                version_match = version_re.search(line.content)
                if version_match is None:
                    continue
                yield Change(
                    name=name_match.group(1),
                    version=version_match.group(1),
                    old=(line.origin == "-"),
                )


def extract_poetry_lock(hunks: Iterable[pygit2.DiffHunk]) -> Generator[Change, None, None]:
    """Each package is denoted by [[package]] and has a name and version field on separate lines.

    Example:
        [[package]]
        name = "wheel"
        version = "0.42.0
    """
    raise NotImplementedError()
    for hunk in hunks:
        pass
