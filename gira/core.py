import sys
from typing import TextIO


class Dependency:
    name: str
    url: str

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def __str__(self):
        return self.name


class Dependencies:
    filetype: str
    dependencies: list[Dependency]

    def __init__(self, filetype, dependencies):
        self.filetype = filetype
        self.dependencies = dependencies

    def __str__(self):
        return f"Dependencies(filetype={self.filetype}, dependencies={self.dependencies})"

    def __iter__(self):
        return iter(self.dependencies)


class Config:
    writer: TextIO = sys.stdout
    strategy = "unstaged"
    dependencies: list[Dependency]


class Change:
    name: str
    version: str
    old: bool

    def __init__(self, name, version, old):
        self.name = name
        self.version = version
        self.old = old

    def __str__(self):
        return f"{self.name}=={self.version}"


class Upgrade:
    name: str
    old_version: str
    new_version: str

    def __init__(self, name, old_version=None, new_version=None):
        self.name = name
        self.old_version = old_version
        self.new_version = new_version

    def __str__(self):
        return f"{self.name}: {self.old_version} => {self.new_version}"
