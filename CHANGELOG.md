# Changelog

All notable changes to watch-vault are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]
- _Add new entries here as you develop; move them under a version on release._

## [0.2.4] — 2026-07-06
### Fixed
- **watch-engine install copied the wrong folder** — the upstream repo has two `scripts/` dirs
  (`scripts/watch.py` and `hooks/scripts/`); the detector matched the hooks one, so `watch.py`
  and the cookie patch never landed (while still printing "✓"). Now locates `scripts/watch.py`
  specifically, derives the skill root from it, and sanity-checks the copy. Found by testing on a
  fresh Mac.

## [0.2.3] — 2026-07-06
### Fixed
- **Installer crashed at vault detection when `WATCH_VAULT_DIR` was unset** (`set -u` unbound
  variable) — anyone without that env var (i.e. most fresh installs) hit it. Now defaults to empty.
  Found by testing on a fresh Mac.

## [0.2.2] — 2026-07-06
### Fixed
- **no-brew installer used the wrong verify flag for yt-dlp** — checked `yt-dlp -version`
  (ffmpeg's flag) instead of `yt-dlp --version`, so a working universal `yt-dlp` binary was
  wrongly reported as failing (false Rosetta warning) and the install aborted. Now uses the
  correct per-binary flag. Found by testing the v0.2.1 install on a fresh Mac.

## [0.2.1] — 2026-07-06
### Fixed
- **macOS without Homebrew** — the installer no longer dies at the dependency step. On a brew-less
  Mac it installs `ffmpeg`/`ffprobe` (evermeet.cx static builds) and `yt-dlp` as **no-sudo binaries**
  in `~/.local/bin`, adds that dir to PATH, and **verifies each binary runs** (with a clear
  Rosetta-2 hint on Apple Silicon if it can't). Found by testing on a fresh Mac.

## [0.2.0] — 2026-07-06
### Added
- **`watch-vault update` subcommand** — update from inside Claude Code (no terminal needed).
  Backed by a self-contained `self_update.py` that re-clones/pulls and reinstalls the skill in
  place, even if the original checkout was deleted.
- **`watch-vault check-updates` / `watch-vault version` subcommands.**
- SKILL.md now routes maintenance subcommands before the watch pipeline.

## [0.1.0] — 2026-07-06
### Added
- **One-command pipeline** (`watch-vault <url>`): watch → auto-categorize → ingest → review HTML → open.
- **Sub-agent + tiered-model routing** (Balanced posture): Sonnet analyst for frame vision/synthesis
  (frames isolated from the main context), Haiku for category, Opus only on low-confidence/long+dense.
- **Resource finder**: web-searches how to install/use any software a video mentions.
- **Reality-check**: scores video claims 1–10 (1 = true, 10 = hype) against web sources, with
  colour-coded badges in the review HTML and an overall `hype_score` in the note.
- **Deterministic scripts** (stdlib-only): `report_to_html.py`, `compact_transcript.py`, `check_updates.py`.
- **YouTube bot-gate bypass**: `WATCH_COOKIES_FROM_BROWSER` passthrough, applied to the upstream
  `watch` engine non-destructively at install.
- **Installer** with system-dep checks, upstream `watch` engine fetch, vault detection/creation,
  ingest-op `CLAUDE.md` template, and interactive config.
- **Update channel**: `update.sh` + `check_updates.py` (GitHub tags).
- Cross-platform review opener (macOS/Linux/WSL).

[Unreleased]: https://github.com/manateeit/watch-vault/compare/v0.2.4...HEAD
[0.2.4]: https://github.com/manateeit/watch-vault/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/manateeit/watch-vault/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/manateeit/watch-vault/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/manateeit/watch-vault/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/manateeit/watch-vault/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/manateeit/watch-vault/releases/tag/v0.1.0
