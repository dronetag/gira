import os
import re
from pathlib import Path
from typing import Optional

import jira
from jira import JIRAError

from . import logger
from .config import ConfigError

_ = JIRAError
_ticket_re = re.compile(r"(?P<ticket>[A-Z]+-\d+)")


def extract_ticket_names(msg: str) -> list[str]:
    return _ticket_re.findall(msg)


class Ticket:
    name: str
    url: str
    summary: str

    def __init__(self, name, url="", summary=""):
        self.name = name
        self.url = url
        self.summary = summary

    def __str__(self) -> str:
        if self.summary:
            return f"{self.name}: {self.summary} ({self.url})"
        if self.url:
            return f"{self.name}: {self.url}"
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


def extract_tickets(msg: str) -> list[Ticket]:
    return [Ticket(name) for name in extract_ticket_names(msg)]


def _get_value(value: Optional[str]):
    filename = ""
    if not value:
        return ""
    elif value.startswith("file://"):
        filename = value[7:]
    elif value.startswith("file:"):
        filename = value[5:]
    elif value.startswith("env://"):
        return os.environ.get(value[6:], "")
    elif value.startswith("env:"):
        return os.environ.get(value[4:], "")
    else:
        return value

    if "$HOME/" in filename:  # because $HOME won't be expanded correctly on Windows
        filename = filename.replace("$HOME/", "~/")
    p = Path(os.path.expandvars(os.path.expanduser(filename)))
    if not p.exists():
        raise ValueError(f"File {p.absolute()} does not exist")
    return p.read_text().strip()


class Jira:
    url: str
    token: Optional[str]
    email: Optional[str]
    projects: list[str]

    _client: Optional[jira.JIRA]

    def __init__(self, url: str = "", token: str = "", email: str = "", **kwargs):
        self.url = url
        self.token = _get_value(token)
        self.email = _get_value(email)
        self.projects = []
        self._client = None
        self._connect_error = 0
        if self.token and not self.url:
            raise ConfigError("jira.token provided without jira.url")

    def connect(self):
        if self.url and self.email and self.token:
            logger.debug(f"Jira connecting to {self.url} with email {self.email} and a token")
            self._client = jira.JIRA(self.url, basic_auth=(self.email, self.token))
        elif self.url and self.token:
            logger.debug(f"Jira connecting to {self.url} with token")
            self._client = jira.JIRA(self.url, token_auth=self.token)
        else:
            logger.debug("No Jira connection details provided")
            self._client = None

    def __str__(self):
        return f"Jira(url={self.url}, token={self.token})"

    def get_ticket_details(self, name: str) -> Optional[Ticket]:
        return self.update_ticket_details(Ticket(name))

    def update_ticket_details(self, ticket: Ticket) -> Optional[Ticket]:
        if self.url:
            ticket.url = (self.url + "/browse/" + ticket.name).replace("//browse", "/browse")

        if self._client is None and self._connect_error == 0:
            try:
                self.connect()
            except jira.exceptions.JIRAError as e:
                if e.status_code == 401:
                    raise ConfigError("Invalid Jira credentials")
                logger.warn(f"Jira connection error: {e.status_code} - {e.text[:50]}...")
                self._connect_error += 1

        if self._client is not None:
            try:
                ticket.summary = self._client.issue(ticket.name, fields="summary").fields.summary
            except jira.JIRAError as e:
                logger.warn(f"{ticket.name}: {e.text} ({e.status_code})")
                logger.debug(str(e))
                return None

        return ticket
