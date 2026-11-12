"""Tests for the `pins-agree` command line."""

import sys
from pathlib import Path

import pytest

from precommit_hooks import cli

CONFIG = """
[[group]]
name = "node"

[[group.pin]]
file = "Dockerfile.ci"
pattern = 'node:(?P<version>[^-@\\s]+)'

[[group.pin]]
file = "ci.yaml"
pattern = 'NODE_VERSION:\\s+(?P<version>\\S+)'
"""


@pytest.fixture
def repo(tmp_path, monkeypatch) -> Path:
    """A repository root, as prek runs hooks from, with agreeing pins."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pins-agree.toml").write_text(CONFIG)
    (tmp_path / "Dockerfile.ci").write_text("FROM node:26.13.0-alpine\n")
    (tmp_path / "ci.yaml").write_text("NODE_VERSION: 26.13.0\n")
    return tmp_path


def run(monkeypatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["pins-agree", *args])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    return int(exc.value.code or 0)


def test_agreeing_pins_exit_0_and_print_nothing(repo, monkeypatch, capsys):
    assert run(monkeypatch) == 0
    assert capsys.readouterr() == ("", "")


def test_disagreeing_pins_exit_1_and_report_on_stderr(repo, monkeypatch, capsys):
    (repo / "ci.yaml").write_text("NODE_VERSION: 24.22.2\n")

    assert run(monkeypatch) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        'pins-agree: group "node": 2 different versions',
        "pins-agree:   Dockerfile.ci:1: 26.13.0",
        "pins-agree:   ci.yaml:1: 24.22.2",
    ]


def test_a_config_error_exits_1_with_one_line_and_no_traceback(repo, monkeypatch, capsys):
    (repo / ".pins-agree.toml").write_text("[[group]\n")

    assert run(monkeypatch) == 1
    err = capsys.readouterr().err
    assert err.startswith("pins-agree: .pins-agree.toml: not valid TOML")
    assert "Traceback" not in err


def test_config_names_another_file(repo, monkeypatch):
    (repo / ".pins-agree.toml").rename(repo / "pins.toml")

    assert run(monkeypatch, "--config", "pins.toml") == 0


def test_version_prints_the_package_version(monkeypatch, capsys):
    from precommit_hooks import __version__

    assert run(monkeypatch, "--version") == 0
    assert capsys.readouterr().out.strip() == __version__


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["--bogus"], id="unknown-flag"),
        pytest.param(["extra"], id="unexpected-argument"),
    ],
)
def test_a_usage_error_exits_2(repo, monkeypatch, argv):
    assert run(monkeypatch, *argv) == 2
