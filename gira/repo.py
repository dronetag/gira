from pathlib import Path
from typing import Optional

import pygit2


class Repo:
    path: str
    ref: str
    bare: bool
    repo: pygit2.Repository

    def __init__(self, path: str, ref: Optional[str] = "", bare: bool = False):
        self.path = path
        self.repo = pygit2.Repository(path, pygit2.GIT_REPOSITORY_OPEN_BARE if bare else 0)
        self.bare = bare
        self.ref = self._check_ref(ref)

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
