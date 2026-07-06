# Roadmap

Direction, not promises. Vote/comment via issues.

## Now (0.1.x)
- Harden the upstream `watch` engine fetch across repo layouts.
- `yt-video-review-eval doctor` command: verify deps, config, vault, and the engine in one shot.
- Config-selectable routing posture actually wired into the SKILL steps (not just documented).

## Next (0.2)
- **Playlists / channels:** ingest a batch of URLs in one run with a summary index note.
- **Dedup / update:** detect an already-ingested video and update its note instead of duplicating.
- **Local-model mode:** route the analyst/researcher to a local OpenAI-compatible endpoint
  (e.g. oMLX) for zero-API-cost runs.
- **Reality-check sources panel:** render the cited sources as a footnotes block in review.html.

## Later
- Non-YouTube parity (podcasts, local files) as first-class inputs with tuned frame budgets.
- A vault "digest" that rolls up the week's watched notes + average hype scores per creator.
- Optional web dashboard over the vault's `watched/` review pages.
- Windows-native (non-WSL) installer path.

## Non-goals
- Re-implementing the `watch` engine (we depend on upstream).
- Storing or transmitting your notes anywhere off your machine.
