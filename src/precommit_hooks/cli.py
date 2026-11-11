"""Command-line entry point for the `pins-agree` hook."""

from __future__ import annotations

import sys
from pathlib import Path

from cyclopts import App

from precommit_hooks import __version__
from precommit_hooks.pins_agree.check import check
from precommit_hooks.pins_agree.config import DEFAULT_PATH, ConfigError, load

app = App(
    name="pins-agree",
    help="Fail when pins that must name one version disagree.",
    version=__version__,
    # main() exits with the returned status; the default action would print it.
    result_action="return_value",
)


@app.default
def pins_agree(*, config: Path = DEFAULT_PATH) -> int:
    """Check that every group in the configuration names one version.

    File globs are relative to the current directory, which is the repository root when prek
    runs the hook.

    Args:
        config: The configuration file.

    Returns:
        0 when every group agrees, 1 when any does not.
    """
    problems = check(load(config), Path.cwd())
    for problem in problems:
        for line in problem.lines():
            print(f"pins-agree: {line}", file=sys.stderr)
    return 1 if problems else 0


def main() -> None:
    """Exit 0 when every group agrees, 1 on a disagreement or a bad config, 2 on a usage error."""
    try:
        status = app()
    except ConfigError as exc:
        print(f"pins-agree: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(status or 0)
