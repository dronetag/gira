from .jira import Jira


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


class Config:
    jira: Jira
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

    def __init__(self, name, old_version=None, new_version=None):
        self.name = name
        self.old_version = old_version
        self.new_version = new_version
        self.tickets = {}

    def __str__(self):
        return f"{self.name} {self.old_version} => {self.new_version}:"
