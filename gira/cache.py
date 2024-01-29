"""cache provides caching of git repositories and basic operations"""

from pathlib import Path

import pygit2

from . import logger

CACHE_DIR = Path(".gira")
MESSAGE_LIMIT = 250


def messages(project: str, url: str, a: str, b: str) -> list[str]:
    """Return commit messages between two revisions a and b"""
    repo_dir = CACHE_DIR / project
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir()

    if not url.startswith("http") and not url.startswith("git@"):
        url = f"https://{url}"
    if not url.endswith(".git"):
        url = f"{url}.git"

    if not repo_dir.exists():
        try:
            logger.debug(f"Cloning {project} with url {url} to {repo_dir}")
            repository = pygit2.clone_repository(url, repo_dir, bare=True)
        except pygit2.GitError:
            logger.error(f"Could not clone {project} with url {url} to {repo_dir}")
            if repo_dir.exists():
                repo_dir.rmdir()
            raise
    else:
        logger.debug(f"Re-useing existing {repo_dir}")
        repository = pygit2.Repository(repo_dir, pygit2.GIT_REPOSITORY_OPEN_BARE)
        logger.debug("Fetching from origin")
        remote = repository.remotes["origin"]
        remote.fetch()

    ending_tag = repository.revparse_single(a)
    starting_tag = repository.revparse_single(b)

    commits = repository.walk(ending_tag.oid)
    messages = []
    for i, commit in enumerate(commits):
        messages.append(commit.message.strip())
        if commit.oid.hex == starting_tag.oid.hex:
            break
        if i >= MESSAGE_LIMIT:
            logger.warning(f"Reached limit of {MESSAGE_LIMIT} commits when going from {a} to {b}")
            break
    return messages
