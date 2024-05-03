import sys
from typing import Optional

import yaml

if sys.version_info >= (3, 11):
    import tomllib as toml
else:
    import tomli as toml
from pathlib import Path

from gira import logger

DEFAULT_CONFIG = Path(".gira.yaml")

logger = logger.getChild("config")


class ConfigError(Exception):
    pass


class Config:
    jira: dict[str, str]  # url, user, token
    observe: dict[str, str]  # name -> url
    submodules: bool

    def __init__(self, jira: dict[str, str], observe: dict[str, str], submodules: bool = True):
        self.jira = jira
        self.observe = observe
        self.submodules = submodules


def from_file(path: Optional[Path]) -> Config:
    """Load configuration file"""
    if path and path.exists():
        return _parse_file(path)

    if DEFAULT_CONFIG.exists():
        return _parse_file(DEFAULT_CONFIG)

    raise FileNotFoundError("No configuration file found")


def _parse_file(path: Path) -> Config:
    config = Config(jira={}, observe={})
    if path.name == ".gira.yaml":
        config = _conf(path)
    elif path.name == "pyproject.toml":
        config = _pytoml(path)
    elif path.suffix in (".yaml", ".yml"):
        config = _generic_yaml(path)
    if not config.observe:
        if not config.submodules:
            raise ConfigError("No observed dependencies and no submodules {path}")
        logger.warn(f"No observed dependencies in {path} - will watch only submodules")
    return config


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
    return Config(jira=_section(parsed, "jira"), observe=_section(parsed, "observe"))


def _generic_yaml(path: Path) -> Config:
    """Parse watched dependencies by GIRA from generic YAML"""
    parsed = yaml.load(path.read_text(), Loader=yaml.SafeLoader)
    return Config(jira=_section(parsed, "gira.jira"), observe=_section(parsed, "gira.observe"))


def _section(d: Optional[dict], path: str) -> dict:
    """Return dot-separated path from dictionary"""
    for key in path.split("."):
        if not d or key not in d:
            return {}
        d = d[key]
    return d or {}
