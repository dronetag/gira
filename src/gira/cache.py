"""cache provides caching of git repositories and basic operations"""

import subprocess
from pathlib import Path

import pygit2  # type: ignore

from . import logger, repo

CACHE_DIR = Path(".gira_cache")


def cache(name: str, url: str) -> pygit2.Repository:
    """Cache a git repository by its url ane name and return a pygit2.Repository object to it"""
    repo_dir = CACHE_DIR / (name + ".git")
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir()

    # add a protocol and .git suffix if missing
    if "://" not in url and not url.startswith("git@"):
        url = f"https://{url}"
    if not url.endswith(".git"):
        url = f"{url}.git"

    # use the binary for remote url to avoid issues with ssh keys
    if not repo_dir.exists():
        logger.debug(f"Cloning {name} with url {url} to {repo_dir}")
        subprocess.run(
            ["git", "clone", "--bare", url, str(repo_dir)], check=True, capture_output=True
        )
    else:
        logger.debug("Fetching from origin")
        # Pass --git-dir explicitly instead of relying on bare-repo discovery via cwd,
        # which git refuses under `safe.bareRepository = explicit`.
        subprocess.run(
            ["git", "--git-dir", str(repo_dir), "fetch", "origin"],
            check=True,
            capture_output=True,
        )
    return repo.Repo(repo_dir, ref="HEAD", bare=True)
