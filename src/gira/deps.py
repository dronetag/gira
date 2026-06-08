"""Dependencies module reads different"""

import re
import sys
from typing import Any, Optional

import yaml

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml
from pathlib import Path

from . import logger

version_re = re.compile(r"""([0-9]+\.[0-9]+[^"',]*)""")

PYTOML_FILENAME = "pyproject.toml"
PUBSPEC_PATTERN = re.compile(r"pubspec.*\.ya?ml")
WEST_PATTERN = re.compile(r"west.*\.ya?ml")
REQUIREMENTS_PATTERN = re.compile(r"requirements.*\.txt")


def is_parsable(filepath: Path) -> bool:
    """Extract changes in observed dependencies from dependency/lock files diffs"""
    return (
        filepath.name == PYTOML_FILENAME
        or PUBSPEC_PATTERN.match(filepath.name) is not None
        or WEST_PATTERN.match(filepath.name) is not None
        or REQUIREMENTS_PATTERN.match(filepath.name) is not None
    )


def parse(path: Path, content: str, observed: dict[str, str]) -> dict[str, str]:
    if path.name == PYTOML_FILENAME:
        return parse_pytoml(content, observed)
    if PUBSPEC_PATTERN.match(path.name) is not None:
        return parse_pubspec_yaml(content, observed)
    if WEST_PATTERN.match(path.name) is not None:
        return parse_west_yaml(content, observed)
    if REQUIREMENTS_PATTERN.match(path.name) is not None:
        return parse_requirements(content, observed)
    raise NotImplementedError(f"No dependency parser for {path.name}")


_name_re = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _requirement_version(line: str) -> Optional[tuple[str, str]]:
    """Return (name, "vX.Y.Z") for a requirement, using the first version in its
    specifier (the lower bound), else None.

    Handles the PEP 508 strings used in project.dependencies,
    project.optional-dependencies and requirements files, with any specifier
    (==, >=, ~=, >, ...). The dronetag convention pins observed dependencies as
    `name >=X.Y.Z, <MAJOR`, so the lower bound is the version being required.
    Environment markers, comments and extras are ignored; unpinned dependencies
    (no version at all) yield None.

    Example:
        "pygit2==1.13.3; os_name != 'nt'"  -> ("pygit2", "v1.13.3")
        "firmware-clients >=1.13.0, <2.0"  -> ("firmware-clients", "v1.13.0")
        "name[extra] ~=1.0.0"              -> ("name", "v1.0.0")
        "dtopener"                         -> None
    """
    line = line.split(";", 1)[0].split("#", 1)[0]  # drop markers and comments
    name_match = _name_re.match(line)
    if name_match is None:
        return None
    name = name_match.group(1)
    specifier = line[name_match.end() :]
    specifier = re.sub(r"^\s*\[[^\]]*\]", "", specifier)  # drop extras like [extra]
    version_match = version_re.search(specifier)
    if version_match is None:
        return None
    return name, "v" + version_match.group(1).strip()


def parse_pytoml(content: str, observed: dict[str, str]) -> dict[str, str]:
    dependencies: dict[str, str] = {}
    parsed = toml.loads(content)

    # project.dependencies and every project.optional-dependencies group share the
    # same PEP 508 requirement format, e.g.
    #     [project]
    #     dependencies = ["pygit2>=1.13.3; os_name != 'nt'", "django==2.1"]
    #     [project.optional-dependencies]
    #     dev = ["ruff==0.4.0"]
    #     test = ["pytest>=8.1.1, <9"]
    requirement_lists: list[Any] = [_section(parsed, "project.dependencies")]
    requirement_lists.extend(_section(parsed, "project.optional-dependencies").values())
    for requirements in requirement_lists:
        if not isinstance(requirements, list):
            continue
        for line in requirements:
            pin = _requirement_version(line)
            if pin is None:
                continue
            name, version = pin
            if name in observed:
                dependencies[name] = version

    if _section(parsed, "tool.poetry.dependencies"):
        """The developer could decide not to version poetry.lock so we need to parse pyproject.toml

        Example:
            [tool.poetry.dependencies]
            python = "^3.8"
            click = "*"
            pymavlink = "^2.4.20"
            ruff = {version="*", optional=true}
        """
        for dependency, value in _section(parsed, "tool.poetry.dependencies").items():
            if dependency not in observed:
                continue
            version = ""
            if isinstance(value, str):
                version = value
            elif isinstance(value, dict) and "version" in value:
                version = value["version"]
            version_match = version_re.search(version)
            if version_match is None:
                continue
            dependencies[dependency] = "v" + version_match.group(1)

    return dependencies


def parse_requirements(content: str, observed: dict[str, str]) -> dict[str, str]:
    """Extract observed dependencies from a pip requirements file.

    Requirements files are the target of setuptools' dynamic dependencies, so a
    project keeping its dependencies out of pyproject.toml is still watched:

        [project]
        dynamic = ["dependencies"]
        [tool.setuptools.dynamic]
        dependencies = {file = ["requirements.txt"]}

    The first version in each specifier (the lower bound) is used, mirroring the
    project.dependencies parsing above. Comments, environment markers and extras
    are ignored.

    Example:
        pygit2 ==1.18.0                       # tracked -> v1.18.0
        dep1-req[extra] >=1.0.0 ; python_version < '3.11'  # tracked -> v1.0.0
        other-lib                             # no version -> skipped
    """
    dependencies: dict[str, str] = {}
    for raw in content.splitlines():
        pin = _requirement_version(raw)
        if pin is None:
            continue
        name, version = pin
        if name in observed:
            dependencies[name] = version

    return dependencies


def parse_pubspec_yaml(content: str, observed: dict[str, str]) -> dict[str, str]:
    """Extracts first-order dependencies from pubspec.yaml

    Example:
        dependencies:
          flutter:
            sdk: flutter
          cupertino_icons: ^1.0.2
          flutter_localizations:
            sdk: flutter
          harald:
            git:
              url: git@github.com:dronetag/harald.git
              ref: v2.70.6
          protocol:
            git:
              url: git@github.com:dronetag/protocol.git
              ref: v2.10.0
              path: dart
          hive: ^2.0.4
    """
    dependencies: dict[str, str] = {}
    parsed = yaml.load(content, Loader=yaml.SafeLoader)
    if not parsed or "dependencies" not in parsed:
        logger.warning("pubspec.yaml is empty or does not contain dependencies")
        return dependencies

    for dependency, value in parsed["dependencies"].items():
        if dependency not in observed:
            continue
        version = ""
        if isinstance(value, str):
            version = "v" + value
        elif isinstance(value, dict):
            if "version" in value:
                version = "v" + value["version"]
            elif "git" in value and "ref" in value["git"]:
                version = value["git"]["ref"]
        dependencies[dependency] = version

    return dependencies


def parse_west_yaml(content: str, observed: dict[str, str]) -> dict[str, str]:
    """Extracts first-order dependencies from pubspec.yaml

    Example:
        manifest:
            version: 0.7

            remotes:
            - name: dronetag
              url-base: git@bitbucket.org:dronetag
            - name: dronetag-git
              url-base: git@github.com:dronetag

            defaults:
                remote: dronetag

            projects:
            - name: nrf
              repo-path: ncs-nrf
              revision: 85a79aa10b9e403fd76e760032ef72057996828c
              import: true
            - name: protocol
              remote: dronetag-git
              path: dt/protocol
              repo-path: protocol
              revision: 963065664406bad9a1b9c985a10f038952397b78
    """
    dependencies: dict[str, str] = {}
    parsed = yaml.load(content, Loader=yaml.SafeLoader)
    if not parsed or "manifest" not in parsed:
        logger.warning("WEST is empty or does not contain dependencies")
        return dependencies

    projects: list[dict[str, Any]] = _section(parsed, "manifest.projects")
    for project in projects:
        dependency = project["name"]
        if dependency not in observed:
            continue
        version = ""
        if "version" in project:
            version = "v" + project["version"]
        elif "revision" in project:
            version = project["revision"]
        dependencies[dependency] = version

    return dependencies


def _section(d: dict[str, Any], path: str) -> Any:
    """Find a deeply nested section of a dict

    :return: empty dict if subsection was not found
    """
    for key in path.split("."):
        if key not in d:
            return {}
        d = d[key]
    return d
