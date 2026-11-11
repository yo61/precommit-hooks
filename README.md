# precommit-hooks

Shared pre-commit hooks, run with [prek](https://github.com/j178/prek), for repositories across
the `yo61`, `horopter-dev` and `ycst-org-uk` orgs.

## `pins-agree`

Fails when pins that must name one version disagree: a Dockerfile's `node:` tag and CI's
`NODE_VERSION`, `go.mod`'s `go` directive and the `golang:` image, the same action version in
several workflows. Renovate and Dependabot update each pin on its own schedule, so a group of
pins can drift apart without either bot noticing; this hook makes that a failed commit and a
failed CI run.

### Use it

In the consuming repository's `.pre-commit-config.yaml`, pinned to a release tag:

```yaml
repos:
  - repo: https://github.com/yo61/precommit-hooks
    rev: v0.1.0
    hooks:
      - id: pins-agree
```

Then list the groups in `.pins-agree.toml` at the repository root:

```toml
[[group]]
name = "node"

[[group.pin]]
file = "Dockerfile.ci"
pattern = '^FROM\s+(?:.*\s)?node:(?P<version>[^-@\s]+)'

[[group.pin]]
file = ".github/workflows/ci.yaml"
pattern = '^\s+NODE_VERSION:\s+"?(?P<version>[^"\s#]+)'

[[group]]
name = "go"

[[group.pin]]
file = "go.mod"
pattern = '^go (?P<version>\S+)$'

[[group.pin]]
file = "Dockerfile.ci"
pattern = 'golang:(?P<version>[^-@\s]+)'
```

### How it checks

- `file` is a glob relative to the repository root (`.github/workflows/*.yaml` matches every
  workflow). It may not be absolute or use `..`.
- `pattern` is a Python regular expression with a named group `version`, searched line by line.
  Every matching line of every matching file is an occurrence, so a second `FROM node:` line or a
  third workflow is checked too.
- A group passes when every occurrence names the same version, compared as exact strings: `26`
  and `26.13.0` disagree, so a floating tag next to an exact version fails.
- A pin whose glob matches no file, or whose pattern matches no line, is a failure rather than a
  pass, so a pattern that has stopped matching cannot hide a drift.
- Unknown keys, a pattern without a `version` group and repeated group names are configuration
  errors.

On a failure the hook prints each group's occurrences, one `file:line: version` per line:

```text
pins-agree: group "node": 2 different versions
pins-agree:   Dockerfile.ci:23: 26.13.0
pins-agree:   .github/workflows/ci.yaml:132: 24.22.2
```

It exits 0 when every group agrees, 1 on a disagreement or a configuration error, and 2 on a
usage error. `--config PATH` reads another file instead of `.pins-agree.toml`.

## Develop

```bash
uv sync
uv run pins-agree --help
```

`task dev:check` is the gate: `ruff check`, `ruff format --check`, `ty check` and `pytest`. Run
it before every commit; CI runs the same checks through the prek hooks in
`.pre-commit-config.yaml`. `task --list` shows every task, and `task dev:hooks-install` installs
the local git hooks.

A hook is a console script in `pyproject.toml` plus an entry in `.pre-commit-hooks.yaml`.
Releases are cut by release-please; consumers pin the `v*` tag, and Dependabot's `pre-commit`
ecosystem moves that pin.

Agent-facing scaffolding lives in `CLAUDE.md` (project instructions), `decisions/` (decision
records) and `quality/criteria.md` (the quality gate).
