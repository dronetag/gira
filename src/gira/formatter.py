from abc import ABC
from typing import Iterable, Optional, TextIO

from .core import Upgrade
from .jira import Ticket


def get_formatter(name: str, stream: TextIO):
    if name in ("commit", "short"):
        return CommitFormatter(stream)
    if name in ("detail", "detailed"):
        return DetailFormatter(stream)
    if name in ("markdown", "md"):
        return MarkdownFormatter(stream)
    raise ValueError(f"Unknown format {name}")


class Formatter(ABC):
    needs_details: bool

    def __init__(self, stream: TextIO):
        self._stream = stream

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]) -> None:
        """Write textual representation of the upgrade and tickets to the internal stream."""


class CommitFormatter(Formatter):
    needs_details = False

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]) -> None:
        chars = 0
        sep = " "
        self._stream.write("\n")
        chars += self._stream.write(f"Dep-Change: {upgrade.name} ")
        if chars > 70:
            chars = self._stream.write("\n    ")

        def _s(s: Optional[str]) -> Optional[str]:  # shorten
            return s[:7] if s and len(s) > 10 else s

        chars += self._stream.write(f"({_s(upgrade.old_version)} -> {_s(upgrade.new_version)})")

        for ticket in tickets:
            if chars + len(ticket.name) >= 70:
                chars += self._stream.write(sep.strip())
                chars = self._stream.write("\n    ") - 1
                sep = ""  # no separator after newline
            chars += self._stream.write(sep)
            sep = ", "
            chars += self._stream.write(ticket.name)


class DetailFormatter(Formatter):
    needs_details = True

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]):
        self._stream.write("\n")
        self._stream.write(f"Dependency change {upgrade}")
        self._stream.write("\n")

        for ticket in tickets:
            if ticket is None:
                continue
            if not ticket.summary:
                self._stream.write(f"  {ticket.name}: {ticket.url}\n")
            else:
                self._stream.write(f"  {ticket.name}: {ticket.summary} ({ticket.url})\n")


class MarkdownFormatter(Formatter):
    needs_details = True

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]):
        self._stream.write("\n")
        self._stream.write(f"### Dependency change {upgrade}")
        self._stream.write("\n")

        for ticket in tickets:
            if ticket is None:
                continue
            if not ticket.summary:
                self._stream.write(f"- {ticket.name}: {ticket.url}\n")
            else:
                self._stream.write(f"- [{ticket.name}]({ticket.url}): {ticket.summary}\n")
