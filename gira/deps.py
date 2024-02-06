"""Dependencies module reads different """
import re
import sys

import yaml

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml
from pathlib import Path

version_re = re.compile(r"""([0-9]+\.[0-9]+[^"',]*)""")
parseable_filenames = ("pyproject.toml", "poetry.lock", "pubspec.yaml", "west.yaml")


def parseable(filepath: Path) -> bool:
    """Extract changes in observed dependencies from dependency/lock files diffs"""
    return filepath.name in parseable_filenames


def parse(path: Path, content: str, observed: dict[str, str]) -> dict[str, str]:
    if path.name == "pyproject.toml":
        return parse_pytoml(content, observed)
    if path.name == "poetry.lock":
        return parse_poetry_lock(content, observed)
    if path.name == "pubspec.yaml":
        return parse_pubspec_yaml(content, observed)
    if path.name == "west.yaml":
        return parse_west_yaml(content, observed)
    raise NotImplementedError(f"No dependency parser for {path.name}")


def parse_pytoml(content: str, observed: dict[str, str]) -> dict[str, str]:
    dependencies: dict[str, str] = {}
    parsed = toml.loads(content)

    if _section(parsed, "project.dependencies"):
        """Parse standart pytoml dependencies definition

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


def parse_poetry_lock(content: str, observed: dict[str, str]) -> dict[str, str]:
    dependencies: dict[str, str] = {}
    parsed = toml.loads(content)

    for package in parsed["package"]:
        if package["name"] not in observed:
            continue
        dependencies[package["name"]] = "v" + package["version"]

    return dependencies


def parse_package_lock(content: str, Set: set[str]) -> dict[str, str]:
    """Extracts first-order dependencies from package-lock.json

    Example:
    {
        "name": "frontend",
        "version": "1.0.0",
        "lockfileVersion": 2,
        "requires": true,
        "packages": {
            "": {
            "name": "frontend",
            "version": "1.0.0",
            "dependencies": {
                "@date-io/date-fns": "^1.3.13",
                "@emotion/react": "^11.9.0",
                "@emotion/styled": "^11.8.1",
                "@fontsource/roboto": "^4.2.3",
                "@fontsource/titillium-web": "^4.5.8",
    """
    raise NotImplementedError("Not implemented parsing dependencies from package.json")


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
    projects: list[dict] = _section(parsed, "manifest.projects")

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


def _section(d, path):
    for key in path.split("."):
        if key not in d:
            return {}
        d = d[key]
    return d
