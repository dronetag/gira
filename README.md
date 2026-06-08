# Gira

> Bring the JIRA tickets behind your dependency bumps straight into your commits and changelogs.

Gira watches your dependency files. When an observed dependency changes version, Gira looks up that
dependency's git repository, collects the commit messages between the old and the new version tag,
extracts the JIRA ticket IDs mentioned there, and prints them — ready to drop into a commit message
or a changelog.

```bash
$ gira
Dep-Change: internal-lib (v1.2.0 -> v1.3.0) OCD-123, OCD-145
```

Gira works great as a [pre-commit](https://pre-commit.com) hook, and equally well standalone for
changelog generation (`gira --format markdown -r <previousTag>`).

> **Pssst:** Gira works best when your dependencies follow
> [semantic release](https://semantic-release.gitbook.io/semantic-release/) and are tagged `vX.Y.Z`.

## Features

- Detects version changes of the dependencies you care about across several ecosystems
- Resolves the JIRA tickets mentioned between the two versions from the dependency's git history
- Three output formats: a short commit suffix, a detailed view, and markdown for changelogs
- First-class [pre-commit](https://pre-commit.com) integration — appends tickets to your commit message
- Optional JIRA connection to enrich tickets with their summaries and URLs
- Git submodules are observed automatically

### Supported dependency files

| File | What Gira reads |
| --- | --- |
| `pyproject.toml` | `[project] dependencies`, every `[project.optional-dependencies]` group, and `[tool.poetry.dependencies]` |
| `requirements*.txt` | exact pins (`name ==X.Y.Z`), including setuptools dynamic dependencies |
| `pubspec.yaml` / `pubspec*.yml` | Dart/Flutter `dependencies` (incl. git `ref`) |
| `west.yml` / `west*.yaml` | Zephyr manifest `projects` (`revision` / `version`) |
| `*.bb` | Yocto/BitBake recipe renames (`pkg_1.0.0.bb` → `pkg_1.1.0.bb`) |
| git submodules | submodule pointer changes |

Gira tracks the version each dependency is pinned to. With a range it uses the lower bound, so the
common `name >=X.Y.Z, <MAJOR` convention works (`>=1.13.0` is tracked as `v1.13.0`, and bumping it to
`>=1.14.0` is reported as `v1.13.0 => v1.14.0`). Entries with no version at all are skipped.

## Installation

Gira is published to the Dronetag package index:

```bash
pip install gira
```

Or install from a checkout:

```bash
pip install .
```

## Usage — standalone

```bash
gira [-r REVISION] [-c CONFIG] [-f commit|detail|markdown] [-a] [-v]
```

| Option | Description |
| --- | --- |
| `-r`, `--ref` | Diff against a specific tag, branch or commit. By default Gira uses staged changes, then unstaged changes, then the previous commit. |
| `-c`, `--config` | Path to the config file (default: `.gira.yaml`). |
| `-f`, `--format` | Output format: `commit` (default, alias `short`), `detail` (alias `detailed`), `markdown` (alias `md`). |
| `-a`, `--all` | Also report changed dependencies that have no JIRA tickets. |
| `-v`, `--verbose` | Verbose/debug logging on stderr. |

Pass `-r <tag>` to diff against a specific revision — handy for building a changelog between two
releases.

> Gira intentionally does nothing inside CI (when the `CI` environment variable is set) and exits
> successfully, so it never interferes with automated commits.

### Output formats

`commit` (default) — a compact suffix for commit messages:

```bash
$ gira
Dep-Change: internal-lib (v1.2.0 -> v1.3.0) OCD-123, OCD-145
```

`detail` — reaches out to JIRA (if configured) for ticket summaries:

```bash
$ gira --format detail
Dependency change internal-lib v1.2.0 => v1.3.0:
  OCD-123: Fix the thing (https://jira.example.com/browse/OCD-123)
  OCD-145: Add the other thing (https://jira.example.com/browse/OCD-145)
```

`markdown` — ideal for changelogs, e.g. between the current tree and a previous tag:

```bash
$ gira --format markdown -r v1.4.0
### Dependency change internal-lib v1.2.0 => v1.3.0:
- [OCD-123](https://jira.example.com/browse/OCD-123): Fix the thing
```

## Usage — pre-commit

```bash
pip install pre-commit
pre-commit install -t prepare-commit-msg -t pre-commit -t commit-msg
```

Add Gira to your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/dronetag/gira
    rev: v1.2.1
    hooks:
    - id: gira
      # if you use a config other than .gira.yaml:
      # args: ["-c", "your-config.yaml"]
```

On `prepare-commit-msg`, Gira appends the discovered tickets to your commit message.

## Configuration

Gira looks for its configuration in this order:

1. the file given with `-c`,
2. `.gira.yaml` in the working directory.

The configuration can live in `pyproject.toml`, a dedicated `.gira.yaml`, or any other YAML file.
Where Gira looks for its keys depends on the file:

| Config file | Observe key | JIRA key |
| --- | --- | --- |
| `pyproject.toml` | `[tool.gira.observe]` | `[tool.gira.jira]` |
| `.gira.yaml` | top-level `observe:` | top-level `jira:` |
| any other `*.yaml` | `gira.observe` | `gira.jira` |

### Observed dependencies

Observed dependencies map a dependency NAME to its git URL. NAME must match the name used in your
dependency/lock file.

```toml
# pyproject.toml
[tool.gira.observe]
internal-lib1 = "github.com/company/internal-lib1"
other-dependency = "bitbucket.com/company/other-dependency"
```

```yaml
# .gira.yaml
observe:
  internal-lib1: "github.com/company/internal-lib1"
  other-dependency: "bitbucket.com/company/other-dependency"
```

The URL may omit the scheme and the `.git` suffix — Gira adds `https://` and `.git` for you. Local
repositories work too via `file:///absolute/path/to/repo.git`.

### setuptools dynamic dependencies

Projects that keep their dependencies out of `pyproject.toml` are still covered, because Gira reads
the referenced `requirements*.txt`:

```toml
[project]
dynamic = ["dependencies"]
[tool.setuptools.dynamic]
dependencies = {file = ["requirements.txt"]}
```

### Submodules

Git submodules are automatically treated as observed dependencies — a change to a submodule pointer
is reported just like a version bump.

### JIRA (optional)

Configuring a JIRA connection lets Gira enrich tickets with their summaries and URLs in the `detail`
and `markdown` formats.

```yaml
# .gira.yaml
jira:
  url: jira.yourcompany.com
  token: your-token
  email: you@yourcompany.com
```

(For `pyproject.toml` use `[tool.gira.jira]`.)

Each of `url`, `token` and `email` can be supplied in several ways, in order of precedence:

1. directly in the config;
2. `env:VARNAME` to read another environment variable, or `file:/path/to/secret` to read a file;
3. a fallback environment variable — `JIRA_URL` / `GIRA_JIRA_URL`, `JIRA_TOKEN` / `GIRA_JIRA_TOKEN`,
   `JIRA_EMAIL` / `GIRA_JIRA_EMAIL`.

This keeps secrets out of your repository:

```yaml
jira:
  url: jira.yourcompany.com
  token: "env:JIRA_TOKEN"
  email: "file:~/.config/jira/email"
```

### Ticket key prefix

By default Gira auto-detects any uppercase JIRA key in the commit messages (`PROJ-123`). If your
project uses a known prefix you can pin it with `jira.prefix`, so only those keys are reported and
unrelated `WORD-123` patterns are ignored:

```yaml
jira:
  prefix: DH          # only DH-123 style keys
```

A list pins several prefixes at once:

```yaml
jira:
  prefix: [DH, OCD]   # DH-123 and OCD-123
```

`prefix` works on its own — no JIRA connection (`url`/`token`/`email`) is required to filter keys.

## How it works

1. Gira diffs your dependency files between two revisions and finds version changes of observed
   dependencies.
2. For each change it clones (or refreshes) the dependency's repository into `.gira_cache/` and walks
   the commits between the old and the new version tag (`vX.Y.Z`).
3. It extracts JIRA ticket IDs (matching `[A-Z]+-\d+`) from those commit messages and renders them in
   the format you chose.
