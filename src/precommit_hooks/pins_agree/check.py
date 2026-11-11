"""Find every occurrence of each group's pins and report the groups that disagree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from precommit_hooks.pins_agree.config import Config, Group, Pin


@dataclass(frozen=True)
class Occurrence:
    """A version written on one line of one file."""

    path: str
    line: int
    version: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.version}"


@dataclass(frozen=True)
class Problem:
    """Something wrong with one group, with the locations that show it."""

    group: str
    summary: str
    details: tuple[str, ...] = ()

    def lines(self) -> list[str]:
        """The problem as report lines: the summary, then each detail indented."""
        return [f'group "{self.group}": {self.summary}', *(f"  {d}" for d in self.details)]


class _Unreadable(Exception):
    def __init__(self, path: str) -> None:
        super().__init__(f"cannot read {path} as UTF-8")


def check(config: Config, root: Path) -> list[Problem]:
    """Check every group in `config` against the files under `root`.

    Args:
        config: The groups to check.
        root: The repository root that each pin's `file` glob is relative to.

    Returns:
        The problems found, in config order; empty when every group agrees.
    """
    problems: list[Problem] = []
    for group in config.groups:
        problems.extend(_check_group(group, root))
    return problems


def _check_group(group: Group, root: Path) -> list[Problem]:
    problems: list[Problem] = []
    found: list[Occurrence] = []
    for number, pin in enumerate(group.pins, start=1):
        try:
            occurrences = _find(pin, root)
        except _Unreadable as exc:
            problems.append(Problem(group.name, f"pin {number}: {exc}"))
            continue
        if occurrences is None:
            problems.append(Problem(group.name, f"pin {number}: no file matches {pin.file!r}"))
        elif not occurrences:
            summary = f"pin {number}: no line in {pin.file!r} matches {pin.pattern.pattern!r}"
            problems.append(Problem(group.name, summary))
        else:
            found.extend(occurrences)
    versions = {occurrence.version for occurrence in found}
    if len(versions) > 1:
        details = tuple(str(occurrence) for occurrence in found)
        problems.append(Problem(group.name, f"{len(versions)} different versions", details))
    return problems


def _find(pin: Pin, root: Path) -> list[Occurrence] | None:
    """Every occurrence of `pin`, or None when its glob matches no file."""
    paths = sorted(path for path in root.glob(pin.file) if path.is_file())
    if not paths:
        return None
    occurrences: list[Occurrence] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise _Unreadable(relative) from None
        for number, line in enumerate(text.splitlines(), start=1):
            match = pin.pattern.search(line)
            if match and match["version"] is not None:
                occurrences.append(Occurrence(relative, number, match["version"]))
    return occurrences
