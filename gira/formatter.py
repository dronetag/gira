from typing import Iterable, TextIO

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


class Formatter:
    needs_details: bool

    def __init__(self, stream: TextIO):
        self._stream = stream

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]):
        raise NotImplementedError()


class CommitFormatter(Formatter):
    needs_details = False

    def print(self, upgrade: Upgrade, tickets: Iterable[Ticket]):
        chars = 0
        sep = " "
        self._stream.write("\n")
        chars += self._stream.write(str(upgrade))
        for ticket in tickets:
            if chars > 72:
                chars += self._stream.write(sep.strip())
                self._stream.write("\n    ")
                sep = ""  # no separator after newline
                chars = 0
            else:
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
                self._stream.write(f"{ticket.name}: {ticket.url}\n")
            else:
                self._stream.write(f"{ticket.name}: {ticket.summary} ({ticket.url})\n")


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
