from dataclasses import dataclass, field
from typing import Optional


@dataclass(order=False, frozen=False)
class Dependency:
    name: str
    url: str = ""
    version: str = ""

    def __str__(self):
        return self.name


@dataclass(order=False, frozen=True)
class Change:
    name: str
    version: str
    old: bool = field(compare=False)

    def __str__(self):
        return f"{self.name}=={self.version}"


@dataclass(order=False, frozen=False)
class Upgrade:
    name: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    messages: list[str] = field(default_factory=list)

    def __str__(self):
        return f"{self.name} {self.old_version} => {self.new_version}:"
