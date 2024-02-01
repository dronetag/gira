# Gira

Gira checks for changes in projects dependencies and prints out all JIRA tags
found in commit messages between old and new version.

Dependency changes are taken from current staged/unstaged or previous commit diff
of available lock files (poetry, pyproject, package-lock...).

Commit messages are taken from projects that follow semantic release (have tags in
`v{X.Y.*}` format).

JIRA tickets are parsed based on a regular expression `[A-Z]+-\d+`.

The unified output is as following

```bash
$ gira
internal-dependency1 <versionB> => <versionB>: JIRA-123, JIRA-567
other-followed-lib <versionB> => <versionB>: JIRA-876, JIRA-543
```

## Configuration

Gira is configured either by pyproject.toml or standalone .gira file. Gira
needs to know the names of followed dependencies and their git urls.

Example config:

```toml
[tool.gira.dependencies]
internal-lib1 = "github.com/company/internal-lib1"
other-dependency = "bitbucket.com/company/other-dependency"
```

## Optional configuration: JIRA

```toml
[tool.gira.jira]
url = "jira.yourcompany.com"
token = "token"
```

If you provide valid JIRA connection infromation the output will change to

```bash
$ gira
internal-dependency1 <versionB> => <versionB>:
  JIRA-123: details about the issue (summary)
  JIRA-567: details about the issue (summary)
```
