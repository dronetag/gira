from typing import Optional, TextIO


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


class Jira:
    url: str
    token: str
    projects: list[str]

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.projects = []

    def __str__(self):
        return f"Jira(url={self.url}, token={self.token})"


class Config:
    jira: Optional[Jira]
    dependencies: dict[str, str]  # name -> url

    def __init__(self, jira, dependencies):
        self.jira = jira
        self.dependencies = dependencies


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
    tickets: dict[str, str]

    def __init__(self, name, old_version=None, new_version=None):
        self.name = name
        self.old_version = old_version
        self.new_version = new_version
        self.tickets = {}

    def __str__(self):
        return f"{self.name} {self.old_version} => {self.new_version}:"

    def to_stream(self, stream: TextIO):
        print(f"{self.name} ({self.old_version} => {self.new_version}):", file=stream, end="")
        sep = " "
        for ticket, title in self.tickets.items():
            if title:
                print(f"\n  {ticket}: {title}", file=stream, end="")
            else:
                print(f"{sep}{ticket}", end="")
                sep = ", "
        print("", file=stream)
