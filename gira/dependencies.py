import sys

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml

from pathlib import Path

from . import logger
from .core import Dependencies, Dependency

DEFAULT_CONFIG_PATHS = (
    ".gira",
    "pyproject.toml",
)


def from_file(path: Path | None) -> Dependencies:
    """Load observed dependencies from configuration file"""
    if path is not None and path.exists():
        return _parse_file(path)

    for path_str in DEFAULT_CONFIG_PATHS:
        if Path(path_str).exists():
            try:
                return _parse_file(Path(path_str))
            except RuntimeError as e:
                logger.debug(str(e))
    raise RuntimeError(
        f"Cannot find valid configuration file in the default paths {DEFAULT_CONFIG_PATHS}"
    )


def _section(d, path):
    for key in path.split("."):
        if key not in d:
            return {}
        d = d[key]
    return d


def _parse_file(path: Path) -> Dependencies:
    logger.debug(f"Loading observed dependencies from {path}")
    if path.name == "pyproject.toml":
        return _pytoml(path)
    if path.name == ".gira":
        return _conf(path)
    raise RuntimeError(f"Unknown configuration file format {path}")


def _pytoml(path: Path) -> Dependencies:
    """Parse watched dependencies by GIRA from pyproject.toml"""
    with open(path, "rb") as f:
        parsed = toml.load(f)
        dependencies: dict[str, str] = _section(parsed, "tool.gira.dependencies")
        filetype = "unknown"
        if _section(parsed, "tool.poetry.dependencies"):
            filetype = "pytoml-poetry"
        if "dependencies" in _section(parsed, "tool.poetry"):
            filetype = "pytoml-poetry"
        elif _section(parsed, "project"):
            filetype = "pytoml"
        else:
            raise RuntimeError(
                "Cannot parse dependencies from pyproject.toml - no [project] nor [tool.poetry]"
            )

        return Dependencies(
            filetype, dependencies=[Dependency(name, url) for (name, url) in dependencies.items()]
        )


def _conf(path: Path) -> Dependencies:
    raise NotImplementedError("TODO: parse .gira configuration file")
