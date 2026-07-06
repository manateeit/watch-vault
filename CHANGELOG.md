# Changelog

## v0.3.0 (2026-01-06)

### Added
- **Workflow automation:** `watch-vault-full.workflow.js` orchestrates batch video ingestion with parallel phases (download → analyze → research → ingest → HTML). Run multiple videos in one command via `/workflows watch-vault-full [url1, url2, ...]` and monitor progress in the workflows dashboard.
- Workflow shows parallelization potential: all downloads run in parallel, all analysts run in parallel, all researchers run in parallel, then ingest and HTML generation.

### Changed
- Updated SKILL.md to document Workflow mode alongside procedural spec.

### Technical
- Workflow uses Sonnet sub-agents for analyst & researcher phases (cost discipline).
- Batch mode automatically routes videos to vault categories based on suggested category from analyst.
- All 4 analysis videos ingested successfully: Portfolio automation (Stock Trading/), Polymarket bot, STORM research, Hermes agent (all AI/).

## v0.2.4 (2026-01-05)

[Previous release notes...]
