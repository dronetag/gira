from pathlib import Path
from typing import Optional, TextIO

from . import cache, config, core, deps, formatter, jira, logger, repo


def gira(config: config.Config, stream: TextIO, format: str, ref: Optional[str]):
    """Main function of gira"""
    fmt = formatter.get_formatter(format, stream)

    # Diff current repository using firstly the revision if specified, then staged changes,
    # unstaged changes and finally try diff with last commit. We use diffs with 3 context lines that
    # are necessary for example for poetry.lock that has records spread over multiple lines
    repository = repo.Repo(Path("."), ref=ref)
    files: list[Path] = repository.changed_files()
    logger.debug(f"Changed files from {repository.ref}: {files}")

    # extract changes from diffs of locks or other dependency specifying files
    upgrades: list[core.Upgrade] = []
    for file in filter(deps.parseable, files):
        logger.debug(f"Processing {file} for dependencies")
        pre = deps.parse(file, repository.get_old_content(file), config.observe)
        post = deps.parse(file, repository.get_current_content(file), config.observe)
        for dep_name in pre.keys():
            if dep_name in post and pre.get(dep_name) != post.get(dep_name):
                upgrades.append(
                    core.Upgrade(
                        name=dep_name, old_version=pre.get(dep_name), new_version=post.get(dep_name)
                    )
                )

    # Added support for submodules - we cannot cache them because they are already "cached" in
    # .git/modules directory. Hence we just get the messages from the submodule repository
    if config.submodules and repository.has_submodules:
        for file in files:
            if file in repository.submodules:
                name = repository.submodules[file]
                module_path = Path(".git/modules/", name)
                old_version, new_version = repository.submodule_change(file)
                upgrades.append(
                    core.Upgrade(
                        name=name,
                        old_version=old_version,
                        new_version=new_version,
                        messages=repo.Repo(module_path, bare=True, ref="HEAD").messages(
                            old_version
                        ),
                    )
                )

    # extract JIRA tickets from commit messages between two tags that follow semantic release
    # modify upgrades by creating dict with keys but empty values (ready for summaries of tickets)
    for upgrade in upgrades:
        if upgrade.messages is None:
            url = config.observe[upgrade.name]  # this might return an object with more information
            try:
                upgrade.messages = cache.cache(upgrade.name, url).messages(
                    upgrade.old_version, upgrade.new_version
                )
            except KeyError as e:
                logger.error(
                    f"Repository {upgrade.name} does not contain {e.args[0]}."
                    " Might have been deleted locally or remotely. Skipping"
                )
                continue
        logger.debug(
            f"Messages for {upgrade.name} between {upgrade.new_version} and"
            f" {upgrade.old_version}: {upgrade.messages}"
        )
        tickets = {ticket for m in upgrade.messages for ticket in jira.extract_ticket_names(m)}

        if len(tickets) == 0:
            logger.info(
                f"No JIRA tickets found in commits for {upgrade.name} between"
                f" {upgrade.new_version} and {upgrade.old_version}"
            )
            continue

        if fmt.needs_details:
            jira_client = jira.Jira(**config.jira)
            fmt.print(upgrade, map(jira_client.get_ticket_details, sorted(tickets)))
        else:
            fmt.print(upgrade, map(jira.Ticket, sorted(tickets)))
