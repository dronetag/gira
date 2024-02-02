"""cache provides caching of git repositories and basic operations"""

import subprocess
from pathlib import Path

import pygit2

from . import logger

CACHE_DIR = Path(".gira_cache")
MESSAGE_LIMIT = 250


def messages(project: str, url: str, a: str, b: str) -> list[str]:
    """Return commit messages between two revisions a and b"""
    repo_dir = CACHE_DIR / (project + ".git")
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir()

    if not url.startswith("http") and not url.startswith("git@"):
        url = f"https://{url}"
    if not url.endswith(".git"):
        url = f"{url}.git"

    # use the binary for remote url to avoid issues with ssh keys
    if not repo_dir.exists():
        logger.debug(f"Cloning {project} with url {url} to {repo_dir}")
        subprocess.run(["git", "clone", "--bare", url, repo_dir], check=True, capture_output=True)
    else:
        logger.debug("Fetching from origin")
        subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True)

    logger.debug(f"Getting commit messages from {a} to {b} (in reverse chronological order)")
    repository = pygit2.Repository(repo_dir, pygit2.GIT_REPOSITORY_OPEN_BARE)
    ending_tag = repository.revparse_single(a)
    starting_tag = repository.revparse_single(b)

    commits = repository.walk(ending_tag.oid)
    messages = []
    for i, commit in enumerate(commits):
        messages.append(commit.message.strip())
        if commit.oid.hex == starting_tag.oid.hex:
            break
        if i >= MESSAGE_LIMIT:
            logger.warning(f"Reached limit {MESSAGE_LIMIT} commits for {project}")
            break
    return messages
