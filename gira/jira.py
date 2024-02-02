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
            return f"{self.name}: {self.summary}\n{self.url}"
        if self.url:
            return f"{self.name}: {self.url}"
        return self.name


class Jira:
    url: str
    token: Optional[str]
    projects: list[str]

    _client = None

    def __init__(self, url: str = "", token: str = "", **kwargs):
        self.url = url
        self.token = token
        self.projects = []
        if url and token:
            self._client = jira.JIRA(url, token_auth=token)
            # or = jira.JIRA(url, basic_auth=(email, token)) # depends on our instance settings

    def __str__(self):
        return f"Jira(url={self.url}, token={self.token})"

    def get_ticket_info(self, name: str) -> Ticket:
        ticket = Ticket(name)

        if self.url:
            ticket.url = (self.url + "/browse/" + name).replace("//", "/")

        if self._client:
            try:
                ticket.summary = self._client.issue(name, fields="summary").fields.summary
            except jira.JIRAError as e:
                logger.error("Could not get JIRA tickets from {config.jira.url}")
                logger.error(str(e))

        return ticket
