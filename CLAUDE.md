# precommit-hooks

Project instructions. The global `~/.claude/CLAUDE.md` still applies; this
covers what it cannot know.

## Gate

`task dev:check` — ruff, ruff format --check, ty, pytest. Run it before every
commit. `task --list` shows everything else.

CI runs the prek hooks from `.pre-commit-config.yaml` rather than restating
them, so a local `task dev:hooks` is the same check CI runs.

## Hooks

A hook is a console script in `pyproject.toml` plus an entry in `.pre-commit-hooks.yaml`.
Consumers install it with prek, which does not read `uv.lock`, so runtime dependencies are
pinned exactly in `pyproject.toml`. A range there would resolve differently on every consumer.

## Commits

Conventional. Types: `build chore ci deps docs feat fix perf refactor revert
style test`. `deps` is non-standard and deliberate — it routes dependency
updates to a visible Dependencies changelog section, where `chore(deps)` would
be hidden and cut no release.

## Agent scaffolding

- `decisions/` — decision records. Grep it before making a choice that
  outlives today's task; add a record when you make a new one.
- `quality/criteria.md` — the criteria a task is checked against before it is
  called done.
