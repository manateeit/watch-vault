# Contributing to watch-vault

Thanks for helping improve it. This is a small, script-first project — contributions stay
easy to review.

## Development model

- **`main`** is always installable. Don't commit directly to it.
- Branch per change: `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`.
- Open a PR into `main`. CI runs `tests/run_tests.sh` (see below).
- Keep changes small and focused; one feature/fix per PR.

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`,
  `docs:`, `chore:`, `refactor:`, `test:`. The subject line is the changelog entry.
- **Versioning:** [SemVer](https://semver.org/). Bump `VERSION`, add a `CHANGELOG.md` entry,
  and tag `vX.Y.Z` on release (that tag is what `check_updates.py` compares against).
- **Scripts:** Python scripts are **stdlib-only** (no pip deps) and ship a `--demo`/`--help`
  self-check. Bash is `set -euo pipefail` and sources `scripts/lib.sh`.
- **The skill contract:** `skills/watch-vault/SKILL.md` is the workflow's source of truth —
  update it when behavior changes, and keep paths generic (`~/.claude/skills/…`, config-driven
  vault) so it works for every user.

## Running tests

```bash
make test          # or: bash tests/run_tests.sh
```
Add a line to `tests/run_tests.sh` for any new script (a `--demo` self-check or an `ast.parse`).

## Releasing

1. `feat`/`fix` PRs merged into `main`.
2. Bump `VERSION`, move `CHANGELOG.md` `[Unreleased]` items under the new version + date.
3. Tag and push: `git tag v0.2.0 && git push --tags`.
4. (Optional) cut a GitHub Release from the tag.

## Ideas / bugs

Open an issue using the templates in `.github/ISSUE_TEMPLATE/`. See `ROADMAP.md` for what's planned.
