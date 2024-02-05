import sys
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml
from pathlib import Path

import yaml

from . import logger
from .jira import Jira

DEFAULT_CONFIG_PATHS = (
    ".gira.yaml",
    "pyproject.toml",
    "west.yml",
    "west.yaml",
)


class Config:
    jira: Jira
    observe: dict[str, str]  # name -> url
    submodules: bool

    def __init__(self, jira, observe, submodules=True):
        self.jira = jira
        self.observe = observe
        self.submodules = submodules


def from_file(path: Optional[Path]) -> Config:
    """Load configuration file"""
    if path and path.exists():
        return _parse_file(path)

    for path_str in DEFAULT_CONFIG_PATHS:
        if Path(path_str).exists():
            logger.debug(f"Loading configuration from {path_str}")
            return _parse_file(Path(path_str))

    raise FileNotFoundError("No configuration file found")


def _parse_file(path: Path) -> Config:
    if path.name == "pyproject.toml":
        return _pytoml(path)
    if path.name == ".gira.yaml":
        return _conf(path)
    if path.name.startswith("west"):
        return _west(path)
    if path.name.endswith(".yaml"):
        return _generic_yaml(path)
    logger.warning("Running with empty configuration")
    return Config(jira=Jira(), observe={})


def _pytoml(path: Path) -> Config:
    """Parse watched dependencies by GIRA from pyproject.toml"""
    with open(path, "rb") as f:
        parsed = toml.load(f)
        return Config(
            jira=_section(parsed, "tool.gira.jira"),
            observe=_section(parsed, "tool.gira.observe"),
        )


def _conf(path: Path) -> Config:
    """Parse watched dependencies by GIRA from .girarc"""
    parsed = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    return Config(jira=Jira(**_section(parsed, "jira")), observe=_section(parsed, "observe"))


def _generic_yaml(path: Path) -> Config:
    """Parse watched dependencies by GIRA from .girarc"""
    parsed = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    return Config(
        jira=Jira(**_section(parsed, "gira.jira")), observe=_section(parsed, "gira.observe")
    )


def _west(path: Path) -> Config:
    parsed = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    jira = _section(parsed, "manifest.gira.jira")
    observe = _section(parsed, "manifest.gira.observe")
    return Config(
        jira=Jira(**jira),
        observe=observe,
    )


def _section(d: Optional[dict], path: str) -> dict:
    """Return dot-separated path from dictionary"""
    for key in path.split("."):
        if not d or key not in d:
            return {}
        d = d[key]
    return d or {}