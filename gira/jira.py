import re
from typing import Iterable

import jira
from jira import JIRAError

_ = JIRAError
_ticket_re = re.compile(r"(?P<ticket>[A-Z]+-\d+)")


def extract_tickets(msg: str) -> list[str]:
    return _ticket_re.findall(msg)


def get_titles(url: str, token: str, tickets: Iterable[str]):
    client = jira.JIRA(url, token_auth=token)
    # or client = jira.JIRA(url, basic_auth=(email, token)) # depends on our instance settings
    return {ticket: client.issue(ticket, fields="summary").fields.summary for ticket in tickets}
