from pathlib import Path
from typing import Optional

import pygit2  # type: ignore

from . import logger


class Repo:
    path: Path
    ref: str
    bare: bool
    repo: pygit2.Repository
    _submodules: Optional[dict[Path, str]]
    MESSAGE_LIMIT = 250

    def __init__(self, path: Path, ref: Optional[str] = "", bare: bool = False):
        self.path = path
        self.repo = pygit2.Repository(str(path), pygit2.GIT_REPOSITORY_OPEN_BARE if bare else 0)
        self.bare = bare
        self.ref = self._check_ref(ref)
        self._submodules = None

    @property
    def has_submodules(self) -> bool:
        """Check if repository has submodules"""
        return len(self.repo.listall_submodules()) > 0

    @property
    def submodules(self) -> dict[Path, str]:
        """Return dict of submodules paths and names"""
        if not self._submodules:
            self._submodules = {Path(s.path): s.name for s in self.repo.submodules}
        return self._submodules

    def changed_files(self) -> list[Path]:
        """List changed filenames in the repository since `self.ref` revision"""
        try:
            diffs = self.repo.diff(self.ref, context_lines=0)
        except KeyError:
            raise RuntimeError(f"Revision {self.ref} does not exist")

        files: set[str] = set()
        for diff in diffs:
            if diff.delta.new_file.path:
                files.add(diff.delta.new_file.path)
        return [Path(s) for s in files]

    def submodule_change(self, submodule_path: Path) -> tuple[str, str]:
        """Return list of lines added and removed in the diff"""
        try:
            diffs = self.repo.diff(self.ref, context_lines=0)
        except KeyError:
            raise RuntimeError(f"Revision {self.ref} does not exist")

        for diff in diffs:
            if Path(diff.delta.new_file.path) == submodule_path:
                old_version = ""
                new_version = ""
                for line in diff.hunks[0].lines:
                    if line.origin == "+":
                        new_version = line.content.strip().split(" ")[-1]
                    if line.origin == "-":
                        old_version = line.content.strip().split(" ")[-1]
                return (old_version, new_version)
        return ("", "")

    def get_current_content(self, path: Path) -> str:
        """Get content of given filepath as it is on the disk right now"""
        if not path.exists():
            raise RuntimeError(f"File {path} does not exist")
        return path.read_text()

    def get_old_content(self, path: Path) -> str:
        """Get content of given filepath on `self.ref` revision"""
        if len(self.ref) == 40:
            commit = self.repo[self.ref]
        else:
            commit = self.repo.references.get(self.ref).peel(pygit2.Commit)
        blob = self.repo[commit.tree[path.as_posix()].id]
        return blob.data.decode("utf-8")

    def _check_ref(self, ref: Optional[str]):
        """Set ref to HEAD if there are any changes, otherwise to HEAD^ (only if empty)"""
        if ref and len(ref) == 40:
            return ref  # it is a commit hash
        if ref and (ref.startswith("HEAD") or ref.startswith("refs/")):
            return ref  # HEAD.* and refs/ qualify as refs
        if ref:
            try:
                self.repo.diff("refs/tags/" + ref)
                return "refs/tags/" + ref
            except KeyError:
                return "refs/heads/" + ref

        if self.repo and len(self.repo.diff("HEAD")) == 0:
            return "HEAD^"

        return "HEAD"

    def messages(self, a: str, b: Optional[str] = None):
        """Get messages between two revisions a and b (in reverse chronological order)

        @throws KeyError in case of invalid references
        """
        logger.debug(f"Getting messages between {a} and {b or self.ref} for {self.path.name}")
        past_commit = self.repo.revparse_single(a)
        current_commit = (
            self.repo.revparse_single(self.ref) if b is None else self.repo.revparse_single(b)
        )

        if not isinstance(past_commit, pygit2.Commit):
            past_commit = past_commit.peel(pygit2.Commit)
        if not isinstance(current_commit, pygit2.Commit):
            current_commit = current_commit.peel(pygit2.Commit)

        if past_commit.commit_time > current_commit.commit_time:
            logger.warning(f"Not getting commit messages for downgrade of {self.path.name}")
            return []

        commits = self.repo.walk(current_commit.oid)
        messages = []
        for i, commit in enumerate(commits):
            messages.append(commit.message.strip())
            if commit.oid.hex == past_commit.oid.hex:
                break
            if i >= Repo.MESSAGE_LIMIT:
                logger.warning(f"Reached limit {Repo.MESSAGE_LIMIT} commits for {self.path.name}")
                break
        return messages
