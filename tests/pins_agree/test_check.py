"""Tests for checking that each group's pins name one version."""

from pathlib import Path

from precommit_hooks.pins_agree.check import check
from precommit_hooks.pins_agree.config import Config, Group, Pin

IMAGE = Pin(file="Dockerfile.ci", pattern=r"^FROM\s+(?:.*\s)?node:(?P<version>[^-@\s]+)")
CI = Pin(file=".github/workflows/*.yaml", pattern=r"^\s+NODE_VERSION:\s+(?P<version>\S+)")


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return tmp_path


def config(*pins: Pin, name: str = "node") -> Config:
    return Config(groups=[Group(name=name, pins=list(pins))])


def lines(problems) -> list[str]:
    return [line for problem in problems for line in problem.lines()]


def test_pins_that_agree_report_nothing(tmp_path):
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "FROM --platform=$BUILDPLATFORM node:26.13.0-alpine@sha256:89 AS c\n",
            ".github/workflows/ci.yaml": "    env:\n      NODE_VERSION: 26.13.0\n",
        },
    )
    assert check(config(IMAGE, CI), root) == []


def test_pins_that_disagree_list_every_location(tmp_path):
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "# header\nFROM node:26.13.0-alpine AS client\n",
            ".github/workflows/ci.yaml": "env:\n  NODE_VERSION: 24.22.2\n",
        },
    )
    assert lines(check(config(IMAGE, CI), root)) == [
        'group "node": 2 different versions',
        "  Dockerfile.ci:2: 26.13.0",
        "  .github/workflows/ci.yaml:2: 24.22.2",
    ]


def test_every_match_counts_so_a_second_copy_that_drifts_is_caught(tmp_path):
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "FROM node:26.13.0-alpine AS build\nFROM node:24.22.2-alpine\n",
            ".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n",
        },
    )
    assert lines(check(config(IMAGE, CI), root))[0] == 'group "node": 2 different versions'


def test_a_glob_matches_every_file_it_names(tmp_path):
    root = repo(
        tmp_path,
        {
            ".github/workflows/a.yaml": "  NODE_VERSION: 26.13.0\n",
            ".github/workflows/b.yaml": "  NODE_VERSION: 24.22.2\n",
        },
    )
    assert lines(check(config(CI), root)) == [
        'group "node": 2 different versions',
        "  .github/workflows/a.yaml:1: 26.13.0",
        "  .github/workflows/b.yaml:1: 24.22.2",
    ]


def test_a_floating_tag_does_not_agree_with_an_exact_version(tmp_path):
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "FROM node:26-alpine\n",
            ".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n",
        },
    )
    assert lines(check(config(IMAGE, CI), root))[0] == 'group "node": 2 different versions'


def test_a_pin_whose_glob_matches_no_file_is_a_problem(tmp_path):
    root = repo(tmp_path, {".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n"})
    assert lines(check(config(IMAGE, CI), root)) == [
        "group \"node\": pin 1: no file matches 'Dockerfile.ci'",
    ]


def test_a_pin_whose_pattern_matches_no_line_is_a_problem(tmp_path):
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "FROM golang:1.27.4-alpine\n",
            ".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n",
        },
    )
    assert lines(check(config(IMAGE, CI), root)) == [
        "group \"node\": pin 1: no line in 'Dockerfile.ci' matches "
        "'^FROM\\\\s+(?:.*\\\\s)?node:(?P<version>[^-@\\\\s]+)'",
    ]


def test_an_optional_version_group_that_did_not_match_is_not_an_occurrence(tmp_path):
    pin = Pin(file="versions", pattern=r"^node(?:=(?P<version>\S+))?$")
    root = repo(tmp_path, {"versions": "node\nnode=26.13.0\n"})
    assert check(config(pin), root) == []


def test_a_file_that_is_not_utf8_is_a_problem(tmp_path):
    (tmp_path / "Dockerfile.ci").write_bytes(b"FROM node:\xff\n")
    root = repo(tmp_path, {".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n"})
    assert lines(check(config(IMAGE, CI), root)) == [
        'group "node": pin 1: cannot read Dockerfile.ci as UTF-8',
    ]


def test_a_directory_matching_the_glob_is_skipped(tmp_path):
    (tmp_path / "Dockerfile.ci").mkdir()
    root = repo(tmp_path, {".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n"})
    assert lines(check(config(IMAGE, CI), root)) == [
        "group \"node\": pin 1: no file matches 'Dockerfile.ci'",
    ]


def test_each_group_is_checked_on_its_own(tmp_path):
    go_mod = Pin(file="go.mod", pattern=r"^go (?P<version>\S+)$")
    golang = Pin(file="Dockerfile.ci", pattern=r"golang:(?P<version>[^-@\s]+)")
    root = repo(
        tmp_path,
        {
            "Dockerfile.ci": "FROM node:26.13.0-alpine\nFROM golang:1.27.4-alpine\n",
            ".github/workflows/ci.yaml": "  NODE_VERSION: 26.13.0\n",
            "go.mod": "module x\n\ngo 1.27.3\n",
        },
    )
    two = Config(
        groups=[
            Group(name="node", pins=[IMAGE, CI]),
            Group(name="go", pins=[go_mod, golang]),
        ]
    )
    assert lines(check(two, root)) == [
        'group "go": 2 different versions',
        "  go.mod:3: 1.27.3",
        "  Dockerfile.ci:2: 1.27.4",
    ]
