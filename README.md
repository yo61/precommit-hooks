# precommit-hooks

Shared pre-commit hooks, run with prek

## Install

```bash
uv sync
```

## Run

```bash
uv run pins-agree --help
```

## Develop

`task dev:check` is the gate: `ruff check`, `ruff format --check`, `ty check`
and `pytest`. Run it before every commit — CI runs the same checks through the
prek hooks in `.pre-commit-config.yaml`.

`task --list` shows every task. `task dev:hooks-install` installs the local
git hooks.

Agent-facing scaffolding lives in `CLAUDE.md` (project instructions),
`decisions/` (decision records), `quality/criteria.md` (the quality gate) and
`docs/superpowers/` (specs and plans).

## Docs

The docs site is in `docs/site/`, built with Fumadocs and published to
<https://yo61.github.io/precommit-hooks/> on every push to `main`.

- `task docs:dev` — hot-reloading site on <http://localhost:3000>
- `task docs:serve` — production build served locally, without the Pages
  `basePath`
- `task docs:build` — production build with the `/precommit-hooks` `basePath`,
  matching CI
