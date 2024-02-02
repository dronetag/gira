import re
from typing import Optional

import jira
from jira import JIRAError

from . import logger

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


class Jira:
    url: str
    token: Optional[str]
    email: Optional[str]
    projects: list[str]

    _client = None

    def __init__(self, url: str = "", token: str = "", email: str = "", **kwargs):
        self.url = url
        self.token = token
        self.email = email
        self.projects = []
        if url and email and token:
            self._client = jira.JIRA(url, basic_auth=(email, token))  # depends on instance settings
        elif url and token:
            self._client = jira.JIRA(url, token_auth=token)
        else:
            self._client = None

    def __str__(self):
        return f"Jira(url={self.url}, token={self.token})"

    def get_ticket_details(self, name: str) -> Optional[Ticket]:
        return self.update_ticket_details(Ticket(name))

    def update_ticket_details(self, ticket: Ticket) -> Optional[Ticket]:
        if self.url:
            ticket.url = (self.url + "/browse/" + ticket.name).replace("//browse", "/browse")

        if self._client:
            try:
                ticket.summary = self._client.issue(ticket.name, fields="summary").fields.summary
            except jira.JIRAError as e:
                logger.warn(f"{ticket.name}: {e.text} ({e.status_code})")
                logger.debug(str(e))
                return None

        return ticket
