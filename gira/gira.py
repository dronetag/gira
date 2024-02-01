import sys
from pathlib import Path
from typing import Optional

from . import cache, config, core, dependencies, jira, logger, repo


def gira(config: config.Config, ref: Optional[str], files: list[str]):
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
    for u in upgrades:
        url = config.dependencies[u.name]  # this might return an object with more information
        messages = cache.messages(u.name, url, u.new_version, u.old_version)
        for message in messages:
            u.tickets.update({k: "" for k in jira.extract_tickets(message)})
        if len(u.tickets) == 0:
            logger.info(
                f"No JIRA tickets found in commits for {u.name} between"
                f" {u.new_version} and {u.old_version}"
            )

    # if we have JIRA connection information then enrich tickets with titles/summaries
    if config.jira:
        try:
            for upgrade in upgrades:
                upgrade.tickets.update(
                    jira.get_titles(config.jira.url, config.jira.token, upgrade.tickets.keys())
                )
        except jira.JIRAError as e:
            logger.error("Could not get JIRA tickets from {config.jira.url}")
            logger.error(str(e))

    # write out upgrades
    for i, upgrade in enumerate(upgrades):
        if len(upgrade.tickets) == 0:
            continue
        if i > 0:
            print("", file=sys.stdout)  # indent each upgrade with empty line
        upgrade.to_stream(sys.stdout)
