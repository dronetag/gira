"""Dependencies module reads different"""

import re
import sys
from typing import Any

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


def is_parsable(filepath: Path) -> bool:
    """Extract changes in observed dependencies from dependency/lock files diffs"""
    return (
        filepath.name == PYTOML_FILENAME
        or PUBSPEC_PATTERN.match(filepath.name) is not None
        or WEST_PATTERN.match(filepath.name) is not None
    )


def parse(path: Path, content: str, observed: dict[str, str]) -> dict[str, str]:
    if path.name == PYTOML_FILENAME:
        return parse_pytoml(content, observed)
    if PUBSPEC_PATTERN.match(path.name) is not None:
        return parse_pubspec_yaml(content, observed)
    if WEST_PATTERN.match(path.name) is not None:
        return parse_west_yaml(content, observed)
    raise NotImplementedError(f"No dependency parser for {path.name}")


def parse_pytoml(content: str, observed: dict[str, str]) -> dict[str, str]:
    dependencies: dict[str, str] = {}
    parsed = toml.loads(content)

    if _section(parsed, "project.dependencies"):
        """Parse standard pytoml dependencies definition

        Example:
            [project]
            ...
            dependencies = [
                "pygit2==1.13.3; os_name != 'nt'",
                "django>2.1; os_name != 'nt'",
            ]
        """
        for line in _section(parsed, "project.dependencies"):
            if "==" not in line:
                continue
            name, version = line.split("==")
            name = name.strip()
            if name not in observed:
                continue
            version_match = version_re.search(version)
            if version_match is None:
                continue
            dependencies[name] = "v" + version_match.group(1)

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
