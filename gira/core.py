from typing import Optional


class Dependency:
    name: str
    url: str
    version: str

    def __init__(self, name, url="", version=""):
        self.name = name
        self.url = url
        self.version = version

    def __str__(self):
        return self.name


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
    old_version: Optional[str]
    new_version: Optional[str]
    messages: Optional[list[str]]

    def __init__(self, name, old_version=None, new_version=None, messages=None):
        self.name = name
        self.old_version = old_version
        self.new_version = new_version
        self.messages = messages

    def __str__(self):
        return f"{self.name} {self.old_version} => {self.new_version}:"
