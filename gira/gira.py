import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO

from . import cache, config, core, dependencies, jira, logger, repo


def gira(config: config.Config, ref: Optional[str], files: list[str] = [], stream=sys.stdout):
    """Main function of gira"""
    # Diff current repository using firstly the revision if specified, then staged changes,
    # unstaged changes and finally try diff with last commit. We use diffs with 3 context lines that
    # are necessary for example for poetry.lock that has records spread over multiple lines
    repository = repo.Repo(".", ref=ref)
    changed_files: list[Path] = []
    if files:
        changed_files.extend(map(Path, files))
        logger.debug(f"Using changed files from args: {files}")
    else:
        changed_files.extend(repository.changed_files())
        logger.debug(f"Using changed files from {repository.ref}: {changed_files}")

    # extract changes from diffs of locks or other dependency specifying files
    upgrades: list[core.Upgrade] = []
    for file in filter(dependencies.parseable, changed_files):
        logger.debug(f"Processing {file} for dependencies")
        pre = dependencies.parse(file, repository.get_old_content(file), config.dependencies)
        post = dependencies.parse(file, repository.get_current_content(file), config.dependencies)
        for dep_name in pre.keys():
            if dep_name in post and pre.get(dep_name) != post.get(dep_name):
                upgrades.append(
                    core.Upgrade(
                        name=dep_name, old_version=pre.get(dep_name), new_version=post.get(dep_name)
                    )
                )

    # extract JIRA tickets from commit messages between two tags that follow semantic release
    # modify upgrades by creating dict with keys but empty values (ready for summaries of tickets)
    for upgrade in upgrades:
        url = config.dependencies[upgrade.name]  # this might return an object with more information
        messages = cache.messages(upgrade.name, url, upgrade.new_version, upgrade.old_version)
        ticket_names = {ticket for m in messages for ticket in jira.extract_ticket_names(m)}
        if len(ticket_names) == 0:
            logger.info(
                f"No JIRA tickets found in commits for {upgrade.name} between"
                f" {upgrade.new_version} and {upgrade.old_version}"
            )
            continue
        _print(upgrade, map(config.jira.get_ticket_info, ticket_names), stream=stream)


def _print(upgrade: core.Upgrade, tickets: Iterable[jira.Ticket], stream: TextIO):
    print(str(upgrade), file=stream, end="")
    sep = " "
    for i, ticket in enumerate(tickets):
        if ticket.summary or ticket.url:
            if i == 0:
                print("", file=stream)  # make a new line for the first ticket
            print(ticket, file=stream)
        else:
            print(f"{sep}{ticket}", file=stream, end="")
            sep = ", "
    print("", file=stream)
