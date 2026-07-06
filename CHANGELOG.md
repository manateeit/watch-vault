# Changelog

## v0.3.1 (2026-01-06)

### Changed
- **Workflow is now the primary batch mode.** Saved at `~/.claude/workflows/watch-vault.js` following Claude Code Workflows specification.
- Users invoke batch with `/watch-vault ["url1", "url2", ...]` (Workflow, not procedural steps)
- Single URLs still work via `watch-vault <url>` (procedural SKILL.md pipeline)
- Workflow phases: Download → Analyze → Research → Ingest → Publish (all parallelizable stages run concurrently)
- Real-time progress tracking via `/workflows` dashboard: monitor agent counts, token usage, drill into phases
- Updated SKILL.md to document Workflow vs. single-URL modes

### Technical
- Workflow uses proper Claude Code Workflow syntax: `export const meta`, `phase()`, `agent()`, `parallel()`
- No file I/O in script itself; all read/write delegated to spawned agents
- Proper error handling and fallback for failed individual videos (rest of batch continues)

## v0.3.0 (2026-01-06)

- Initial Workflow automation attempt (framework only, not properly integrated)

## v0.2.4 (earlier)

[Previous release notes...]
