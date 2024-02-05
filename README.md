# Gira

Gira gathers JIRA tickets from commit messages of your updated dependencies when you
change them in one of: `pyproject.toml`, `poetry.lock`, `west.yaml`, and `pubspec.yaml`.
It is especially usefull in "prepare-commit-msg" stage of [pre-commit](https://pre-commit.com)

//Disclaimer: works the best if your dependencies follow [semantic release](https://semantic-release.gitbook.io/semantic-release/) (have tags in `v{X.Y.*}` format)//


## Usage

```bash
gira [-r revision] [--format="commit|detail|markdown"]
```

Revision can be tag/branch or a commit. Gira will check dependency files for changes between
the current version and the revision version.

Format is useful if you generate into a commit message (only ticket names (e.g. JIRA-1234))
or you want a user readable "detailed" print or the same but markdown formatted.

```bash
$ gira [--format=commit]
internal-dependency1 <versionB> => <versionB>: JIRA-123, JIRA-567
other-followed-lib <versionB> => <versionB>: JIRA-876, JIRA-543
```

## Configuration

Gira is configured either by pyproject.toml or standalone .gira.yaml or actually any other
YAML file that you specify with `-c` and has "gira.observe" and optionally "gira.jira" keys.

### Observed Dependencies

Observed dependencies are in form of NAME=git-url where NAME must be the same as specified
in your dependency file (e.g. pyproject.toml or a YAML).

```toml
[tool.gira.observe]
internal-lib1 = "github.com/company/internal-lib1"
other-dependency = "bitbucket.com/company/other-dependency"
```

### Submodules

Submodules are automatically added into observed dependencies. You can turn off support
for submodules by settings `gira.submodules=false` in your config file.


### JIRA (optional)

Example of a YAML configuration file section for JIRA (for pyproject.toml use `tool.gira.jira`).
Token and email can be passed via environment variables `JIRA_TOKEN` or `GIRA_JIRA_TOKEN` and
`JIRA_EMAIL` or `GIRA_JIRA_EMAIL`.

```yaml
jira:
  url: jira.yourcompany.com
  token: token
  email: your@email.com
```

Setting JIRA connection information allows for "detailed" and "markdown" formatting of the output
as follows:

```bash
$ gira
internal-dependency1 <versionB> => <versionB>:
  JIRA-123: details about the issue (url)
  JIRA-567: details about the issue (url)
```
