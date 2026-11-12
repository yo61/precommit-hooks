"""Tests for loading and validating `.pins-agree.toml`."""

from pathlib import Path

import pytest

from precommit_hooks.pins_agree.config import ConfigError, load

NODE = """
[[group]]
name = "node"

[[group.pin]]
file = "Dockerfile.ci"
pattern = 'node:(?P<version>[^-@\\s]+)'

[[group.pin]]
file = ".github/workflows/ci.yaml"
pattern = 'NODE_VERSION:\\s+(?P<version>\\S+)'
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".pins-agree.toml"
    path.write_text(text)
    return path


def test_a_valid_config_loads_its_groups_and_pins(tmp_path):
    config = load(write(tmp_path, NODE))

    [group] = config.groups
    assert group.name == "node"
    assert [pin.file for pin in group.pins] == ["Dockerfile.ci", ".github/workflows/ci.yaml"]
    match = group.pins[0].pattern.search("FROM node:26.13.0-alpine")
    assert match is not None
    assert match["version"] == "26.13.0"


def test_a_missing_file_says_how_to_create_one(tmp_path):
    with pytest.raises(ConfigError, match=r"\.pins-agree\.toml: not found; create it"):
        load(tmp_path / ".pins-agree.toml")


def test_invalid_toml_is_reported_with_the_path(tmp_path):
    with pytest.raises(ConfigError, match=r"\.pins-agree\.toml: not valid TOML"):
        load(write(tmp_path, "[[group]\n"))


def test_a_config_with_no_groups_is_rejected(tmp_path):
    with pytest.raises(ConfigError, match="group: Field required"):
        load(write(tmp_path, ""))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param(
            NODE.replace("(?P<version>[^-@\\s]+)", "([^-@\\s]+)"),
            r"group\.0\.pin\.0\.pattern: must have a named group \(\?P<version>\.\.\.\)",
            id="pattern-without-version-group",
        ),
        pytest.param(
            NODE.replace("node:(?P<version>", "node:(?P<version"),
            r"group\.0\.pin\.0\.pattern: .*regular expression",
            id="pattern-that-does-not-compile",
        ),
        pytest.param(
            NODE.replace('file = "Dockerfile.ci"', 'file = "/etc/Dockerfile"'),
            r"group\.0\.pin\.0\.file: must be relative to the repository root",
            id="absolute-file",
        ),
        pytest.param(
            NODE.replace('file = "Dockerfile.ci"', 'file = "../Dockerfile.ci"'),
            r"group\.0\.pin\.0\.file: must be relative to the repository root",
            id="file-outside-the-repository",
        ),
        pytest.param(
            NODE.replace('file = "Dockerfile.ci"', 'file = ""'),
            r"group\.0\.pin\.0\.file: String should have at least 1 character",
            id="empty-file",
        ),
        pytest.param(
            NODE.replace('name = "node"', 'name = "node"\nrequired = true'),
            r"group\.0\.required: Extra inputs are not permitted",
            id="unknown-key",
        ),
        pytest.param(
            '[[group]]\nname = "node"\n',
            r"group\.0\.pin: Field required",
            id="group-without-pins",
        ),
        pytest.param(
            NODE + NODE,
            r"group: names must be unique; repeated: node",
            id="duplicate-group-names",
        ),
    ],
)
def test_an_invalid_config_names_the_field_and_the_problem(tmp_path, text, message):
    with pytest.raises(ConfigError, match=message):
        load(write(tmp_path, text))
