# Gira

Gira checks for changes in projects dependencies and prints out all JIRA tags
found in commit messages between old and new version.

Dependency changes are taken from current state versus previous commit or tag
from all available lock files (poetry, pyproject, package-lock...).

The unified output is as following

```bash
$ gira
internal-dependency1: JIRA-123, JIRA-567
other-followed-lib: JIRA-876, JIRA-543
```

## Configuration

Gira is configured either by pyproject.toml or standalone .gira file. Gira
needs to know the names of followed dependencies and their git urls.

Example config:

```toml
[dependencies]
internal-lib1 = "github.com/company/internal-lib1"
other-dependency = "bitbucket.com/company/other-dependency"
```

