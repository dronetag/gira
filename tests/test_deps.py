"""Unit tests for gira.deps - parsing dependency files for observed version changes.

These tests exercise the installed ``gira`` package (src/ layout), so run them
after ``pip install -e .[dev]`` or against the built package, never by adding
``src`` to the path.
"""

from pathlib import Path

import pytest

from gira import deps


# --------------------------------------------------------------------------- #
# is_parsable / parse dispatch
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name",
    [
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements.test.txt",
        "pubspec.yaml",
        "pubspec.yml",
        "pubspec-prod.yaml",
        "west.yml",
        "west.yaml",
        "west-something.yaml",
    ],
)
def test_is_parsable_true(name):
    assert deps.is_parsable(Path(name))
    # also matches when nested in a sub-directory (only the filename matters)
    assert deps.is_parsable(Path("some/sub/dir") / name)


@pytest.mark.parametrize(
    "name",
    ["setup.py", "README.md", "poetry.lock", "foo.txt", "requirements.cfg", "pubspec.json"],
)
def test_is_parsable_false(name):
    assert not deps.is_parsable(Path(name))


def test_parse_dispatches_by_filename():
    observed = {"dep": "url"}
    assert deps.parse(
        Path("a/pyproject.toml"), '[project]\ndependencies=["dep==1.0.0"]\n', observed
    )
    parsed = deps.parse(Path("a/requirements.txt"), "dep==1.0.0\n", observed)
    assert len(parsed) == 1
    assert parsed["dep"].version == "v1.0.0"


def test_parse_unknown_file_raises():
    with pytest.raises(NotImplementedError):
        deps.parse(Path("unknown.lock"), "", {})


# --------------------------------------------------------------------------- #
# _requirement_version - the shared PEP 508 line parser
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "line, expected",
    [
        ("pygit2==1.13.3", ("pygit2", "v1.13.3")),
        ("pygit2 ==1.13.3", ("pygit2", "v1.13.3")),
        ("firmware-clients >=1.13.0, <2.0", ("firmware-clients", "v1.13.0")),
        ("dtproto >= 2.27.0", ("dtproto", "v2.27.0")),
        ("dt_fwinfo>=1.3.0,<2.0", ("dt_fwinfo", "v1.3.0")),
        ("name[extra] ~=1.0.0", ("name", "v1.0.0")),
        ("django>2.1", ("django", "v2.1")),
        ("pkg==1.2.3; os_name != 'nt'", ("pkg", "v1.2.3")),
        ("pkg==1.2.3  # a comment", ("pkg", "v1.2.3")),
        ("  pkg == 1.2.3  ", ("pkg", "v1.2.3")),
        ("dotted.name==1.2.0", ("dotted.name", "v1.2.0")),
    ],
)
def test_requirement_version_match(line, expected):
    assert deps._requirement_version(line) == expected


@pytest.mark.parametrize(
    "line",
    [
        "dtopener",  # no version at all
        "dtopener  # only a comment",
        "",  # empty
        "   ",  # whitespace
        "# fully commented line",
        "pkg==1",  # needs at least MAJOR.MINOR to match version_re
    ],
)
def test_requirement_version_none(line):
    assert deps._requirement_version(line) is None


# --------------------------------------------------------------------------- #
# parse_pytoml
# --------------------------------------------------------------------------- #
def test_parse_pytoml_dependencies_and_optional_groups():
    content = """
    [project]
    name = "x"
    dependencies = [
        "dep-pin==1.0.0",
        "dep-range >=2.4.0, <3.0",
        "not-observed==9.9.9",
        "unversioned",
    ]
    [project.optional-dependencies]
    dev = ["ruff==0.4.0", "dep-dev ~=1.5.0"]
    test = ["dep-test >=3.1.0"]
    """
    observed = {"dep-pin": "u", "dep-range": "u", "dep-dev": "u", "dep-test": "u"}
    parsed = deps.parse_pytoml(content, observed)
    assert len(parsed) == 4
    assert parsed["dep-pin"].version == "v1.0.0"
    assert parsed["dep-range"].version == "v2.4.0"
    assert parsed["dep-dev"].version == "v1.5.0"
    assert parsed["dep-test"].version == "v3.1.0"


def test_parse_pytoml_only_returns_observed():
    content = '[project]\ndependencies = ["a==1.0.0", "b==2.0.0"]\n'
    parsed = deps.parse_pytoml(content, {"b": "u"})
    assert len(parsed) == 1
    assert parsed["b"].version == "v2.0.0"


def test_parse_pytoml_poetry_string_and_dict():
    content = """
    [tool.poetry.dependencies]
    python = "^3.8"
    dep-str = "^2.4.20"
    dep-dict = {version = "1.7.0", optional = true}
    dep-star = "*"
    """
    observed = {"dep-str": "u", "dep-dict": "u", "dep-star": "u"}
    # dep-star ("*") has no version and is skipped
    parsed = deps.parse_pytoml(content, observed)
    assert len(parsed) == 2
    assert parsed["dep-str"].version == "v2.4.20"
    assert parsed["dep-dict"].version == "v1.7.0"


def test_parse_pytoml_empty():
    assert deps.parse_pytoml('[project]\nname = "x"\n', {"dep": "u"}) == {}


# --------------------------------------------------------------------------- #
# parse_requirements
# --------------------------------------------------------------------------- #
def test_parse_requirements():
    content = """
    # a comment line
    click
    dep-pin ==1.18.0
    dep-range[extra] >=1.0.0, <2.0 ; python_version < '3.11'
    dep-loose >2.1.3   # inline comment
    not-observed ==9.9.9

    """
    observed = {"dep-pin": "u", "dep-range": "u", "dep-loose": "u"}
    parsed = deps.parse_requirements(content, observed)
    assert len(parsed) == 3
    assert parsed["dep-pin"].version == "v1.18.0"
    assert parsed["dep-range"].version == "v1.0.0"
    assert parsed["dep-loose"].version == "v2.1.3"


def test_parse_requirements_empty():
    assert deps.parse_requirements("", {"dep": "u"}) == {}


# --------------------------------------------------------------------------- #
# parse_pubspec_yaml
# --------------------------------------------------------------------------- #
def test_parse_pubspec_yaml():
    content = """
    name: app
    dependencies:
      cupertino_icons: ^1.0.2
      harald:
        git:
          url: git@github.com:dronetag/harald.git
          ref: v2.70.6
      pinned:
        version: 1.2.3
      flutter:
        sdk: flutter
      not-observed: ^9.9.9
    """
    observed = {"cupertino_icons": "u", "harald": "u", "pinned": "u", "flutter": "u"}
    parsed = deps.parse_pubspec_yaml(content, observed)
    assert len(parsed) == 4
    assert parsed["cupertino_icons"].version == "v^1.0.2"  # string value is prefixed verbatim
    assert parsed["harald"].version == "v2.70.6"  # git ref used as-is
    assert parsed["pinned"].version == "v1.2.3"  # dict with explicit version
    assert parsed["flutter"].version == ""  # sdk dependency carries no version


def test_parse_pubspec_yaml_empty_or_missing_dependencies():
    assert deps.parse_pubspec_yaml("", {"dep": "u"}) == {}
    assert deps.parse_pubspec_yaml("name: app\n", {"dep": "u"}) == {}


# --------------------------------------------------------------------------- #
# parse_west_yaml
# --------------------------------------------------------------------------- #
def test_parse_west_yaml():
    content = """
    manifest:
      projects:
        - name: by-revision
          revision: 85a79aa10b9e403fd76e760032ef72057996828c
        - name: by-tag
          revision: v1.4.0
        - name: by-version
          version: "2.5.0"
        - name: not-observed
          revision: deadbeef
    """
    observed = {"by-revision": "u", "by-tag": "u", "by-version": "u"}
    parsed = deps.parse_west_yaml(content, observed)
    assert len(parsed) == 3
    assert parsed["by-revision"].version == "85a79aa10b9e403fd76e760032ef72057996828c"
    assert parsed["by-tag"].version == "v1.4.0"
    assert parsed["by-version"].version == "v2.5.0"


def test_parse_west_yaml_empty_or_missing_manifest():
    assert deps.parse_west_yaml("", {"dep": "u"}) == {}
    assert deps.parse_west_yaml("other: value\n", {"dep": "u"}) == {}


def test_parse_toml_extra_specifiers():
    # tested specifiers: ==, >=, ~=, extras, unpinned
    observed = {"a", "b", "c", "d", "e"}
    content = """
    [project]
    name = "x"
    dependencies = [
        "a >=1.13.0, <2.0",
        "b ==0.14.0",
        "c[extra] ~=2.3.4 ; python_version < '3.11'",
        "d > 2.1",
        "e",
    ]
    """
    parsed = deps.parse_pytoml(content, observed)
    assert len(parsed) == 4
    assert parsed["a"].version == "v1.13.0"
    assert parsed["b"].version == "v0.14.0"
    assert parsed["c"].version == "v2.3.4"
    assert parsed["d"].version == "v2.1"


# --------------------------------------------------------------------------- #
# _section
# --------------------------------------------------------------------------- #
def test_section_nested_lookup():
    data = {"tool": {"gira": {"observe": {"a": "u"}}}}
    assert deps._section(data, "tool.gira.observe") == {"a": "u"}


def test_section_missing_returns_empty_dict():
    assert deps._section({"tool": {}}, "tool.gira.observe") == {}
    assert deps._section({}, "a.b.c") == {}
