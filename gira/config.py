import sys
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml
from pathlib import Path

import yaml

from . import logger
from .core import Config

DEFAULT_CONFIG_PATHS = (
    ".gira.yaml",
    "pyproject.toml",
)


def from_file(path: Optional[Path]) -> Config:
    """Load observed dependencies from configuration file"""
    if path and path.exists():
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


def _parse_file(path: Path) -> Config:
    logger.debug(f"Loading observed dependencies from {path}")
    if path.name == "pyproject.toml":
        return _pytoml(path)
    if path.name == ".gira.yaml":
        return _conf(path)
    raise RuntimeError(f"Unknown configuration file format {path}")


def _pytoml(path: Path) -> Config:
    """Parse watched dependencies by GIRA from pyproject.toml"""
    with open(path, "rb") as f:
        parsed = toml.load(f)
        return Config(
            jira=_section(parsed, "tool.gira.jira"),
            dependencies=_section(parsed, "tool.gira.dependencies"),
        )


def _conf(path: Path) -> Config:
    """Parse watched dependencies by GIRA from .girarc"""
    parsed = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    return Config(jira=parsed.get("jira", {}), dependencies=parsed.get("dependencies", {}))


def _west(path: Path) -> Config:
    _ = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    raise NotImplementedError("Not implemented yet")
