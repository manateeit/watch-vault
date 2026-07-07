---
name: yt-video-review-eval
description: >
  One-shot pipeline: given a YouTube (or any yt-dlp / local) video URL, watch it,
  auto-pick the best Obsidian-vault category, research how to get any software/links
  it mentions, run a scored 1–10 reality-check (1=true, 10=hype) on its claims,
  ingest the analysis, generate a self-contained review HTML page (with colour-coded
  hype badges), save that HTML in the vault next to the report, and open it. Runs the
  token-heavy vision/synthesis and web research in Sonnet sub-agents so frames and
  fetched pages never bloat the main context. Use when the user gives a video URL and
  wants it watched AND filed into their vault — "watch and ingest this",
  "yt-video-review-eval <url>", "add this video to my vault", or just pastes a URL. Also handles
  maintenance subcommands: "yt-video-review-eval update", "yt-video-review-eval check for updates",
  "yt-video-review-eval version".
---

# yt-video-review-eval

Chains **/watch → vault ingest → review HTML** into a single run from just a URL.
Designed for **token discipline**: mechanical steps are scripts (zero LLM), the
expensive frame-vision + report synthesis is delegated to **one Sonnet sub-agent**
(so ~50–80k image tokens live in *its* context, not the main thread), and Opus is
reserved for genuinely hard cases only.

**Absolute paths (this machine):**
- watch:      `~/.claude/skills/watch/scripts/watch.py`
- setup:      `~/.claude/skills/watch/scripts/setup.py`
- transcript: `~/.claude/skills/yt-video-review-eval/scripts/compact_transcript.py`
- html gen:   `~/.claude/skills/yt-video-review-eval/scripts/report_to_html.py`

## Subcommands (handle these BEFORE the pipeline)
If the user's message is a maintenance command rather than a URL, do that instead of watching:

- **`yt-video-review-eval update`** / "update yt-video-review-eval" / "update my copy" →
  run `python3 ~/.claude/skills/yt-video-review-eval/scripts/self_update.py`, relay the result, and
  remind them to **restart Claude Code** so the new `SKILL.md` loads. (Self-contained — it
  re-clones if the original checkout is gone.)
- **`yt-video-review-eval check-updates`** / "is there a yt-video-review-eval update?" →
  run `python3 ~/.claude/skills/yt-video-review-eval/scripts/check_updates.py` and relay its one-liner.
- **`yt-video-review-eval version`** → print the `version` from `~/.config/yt-video-review-eval/config.toml`.

Anything that contains a video URL falls through to the pipeline below.

## Batch Mode (NEW — v0.3.1)

For ingesting **multiple videos in one run**, use the **Workflow:**
```
/yt-video-review-eval ["https://youtu.be/...", "https://youtu.be/...", ...]
```

The Workflow (saved at `~/.claude/workflows/yt-video-review-eval.js`) orchestrates the entire pipeline in parallel:
- **Phase 1 (Download):** All videos download in parallel via `watch.py`
- **Phase 2 (Analyze):** Sonnet analysts fill reports for each video in parallel
- **Phase 3 (Research):** Sonnet researchers add Resources & Reality-check for each in parallel
- **Phase 4 (Ingest):** Move reports/frames to vault, append to log.md, create topic notes
- **Phase 5 (Publish):** Generate HTML reviews for each video

**Key differences from single-URL skill:**
- Single URL: `yt-video-review-eval https://youtu.be/...` (runs via procedural SKILL.md steps)
- Multiple URLs: `/yt-video-review-eval ["url1", "url2", ...]` (runs as Workflow with `/workflows` progress view)
- Workflow shows real-time progress, agent counts, token totals, elapsed time
- Use `/workflows` to monitor, pause, resume, or drill into individual phases/agents
- All parallelizable steps (download, analyze, research, HTML generation) run concurrently

## Model & sub-agent routing (cost discipline — follow this)

| Stage | Runs as | Model | Why |
|-------|---------|-------|-----|
| download · frame extract · transcript compaction · HTML gen · file moves | **scripts** | none | deterministic, **0 tokens** |
| frame vision + fill all report sections | **`watch-analyst` sub-agent** | **Sonnet** (all videos) | vision + solid writing at ~⅕ Opus cost; **frames stay in the sub-agent's context** |
| web research: resources + reality-check | **`watch-researcher` sub-agent** (WebSearch/WebFetch) | **Sonnet** | fetched pages stay in *its* context; returns two distilled sections |
| category classification | analyst *suggests*; orchestrator confirms vs vault `CLAUDE.md` | **Haiku** if a standalone check is needed | one-label decision — never spend Opus here |
| ingest: log line + topic note (+ cross-links) | orchestrator (reads the **text-only** filled report) | session model | cheap (no images); needs vault judgment |
| hard-case QA | **`watch-reviewer` sub-agent**, *only if* `confidence=low` **or** (`duration > 30 min` **and** dense/technical) | **Opus** | deliberate escalation, not by default |
| orchestration + user summary | main loop | session model | glue |

**Posture: BALANCED.** Analyst = **Sonnet always**; category = **Haiku**; **Opus reviewer
only** when the analyst returns `confidence=low` OR the video is `>30 min AND dense`;
**frame-read cap = 15** (hero + spread); transcript always read in full (cheap).
Never read frames in the main thread; never use Opus for a step Sonnet or a script can do.

## Step 0 — Load config
Read `~/.config/yt-video-review-eval/config.toml` (created by the installer). Honor:
`vault_dir`, `open_command` (macOS `open` · Linux `xdg-open` · WSL `explorer.exe`),
`cookies_from_browser`, `whisper_backend`, `routing_posture`, `max_frames`,
`reality_check`, `resource_finder`, `auto_open_review`, and the optional `[thalix]` block
(`enabled` default false). Env vars override the file. If the file is missing, fall back to
sane defaults (auto-detect vault, `open`, no cookies, Balanced posture, cap 15,
reality-check on, thalix off).

## Step 1 — Preflight (skip if already green this session)
`python3 <setup.py> --check` → on non-zero follow the /watch setup table. **Bot-gate
fix:** if yt-dlp fails with *"Sign in to confirm you're not a bot"*, set
`WATCH_COOKIES_FROM_BROWSER=safari` (or `chrome`/`firefox`, whichever is logged into
YouTube) — the /watch downloader now passes it through. `WATCH_COOKIES_FILE=<cookies.txt>`
also works. Probe with `yt-dlp --cookies-from-browser safari --skip-download --print title <url>`.

## Step 2 — Watch (script, 0 tokens)
Infer a one-line intent from the user's words (else "general summary").
```
# prefix with WATCH_COOKIES_FROM_BROWSER=<cookies_from_browser from config> if the gate hits
python3 <watch.py> "<url>" --intent "<intent>"
```
Capture the printed **workdir** + `report.md` path.

## Step 3 — Delegate the heavy analysis to the `watch-analyst` sub-agent (Sonnet)
Spawn **one** sub-agent (**model=sonnet**) with this task, and **do not read the frames
yourself**:
> Run `compact_transcript.py <workdir>/report.md --out <workdir>/paras.txt` and read
> it in full. Read the 5 hero frames (from the report frontmatter) plus an evenly-spread
> sample of others — a **hard cap of 15 frame reads total**, never all 80–100. Then fill
> EVERY `<!-- pending Claude fill: … -->` marker in `<workdir>/report.md` via Edit (TL;DR,
> key moments, hook microscope, editorial profile, quotables, entities as `[[wikilinks]]`,
> concepts). Also add `creator:` and a suggested `category:` line to the frontmatter.
> Return ONLY: title, duration, creator, suggested category + one-line reason, a 4–6
> sentence summary, ⚠️ promo/unverified flags, `confidence: high|low`, and `dense: yes|no`.

The sub-agent returns text; the frames stay in its context. Verify with
`grep -c 'pending Claude fill'` == 0.

**Escalation (BALANCED posture):** spawn a `watch-reviewer` sub-agent (**model=opus**) to
audit/repair the report before ingest **only if** the analyst returns `confidence: low`
**or** (`duration > 30 min` **and** `dense: yes`). Otherwise proceed straight to ingest —
do **not** spend Opus on the common case.

## Step 3.5 — Resources + reality-check (`watch-researcher` sub-agent, Sonnet + web)
Spawn one sub-agent (**model=sonnet**, with WebSearch/WebFetch) so fetched pages stay
out of the main thread. Give it the report's Entities + Quotable-moments + key factual
claims. It must **append two new `##` sections to `<workdir>/report.md`** (before
`## Transcript`) and return the overall hype score:

1. **`## Resources & how to get them`** — for every software / tool / site mentioned,
   web-search the **official source** and write: official URL + repo, **how to install**
   (GUI and/or CLI, prerequisites), how to use it, and a "learn more"/docs link. Group by
   tool. Budget: ~1–2 searches per distinct tool; don't fetch more than needed.

2. **`## Reality check (1 = true · 10 = hype)`** — fact-check the video's notable claims.
   Score each on this scale (**1 = true, 10 = not true / hype**), lower = more trustworthy:
   > 1–2 verified true · 3–4 mostly true (minor caveats) · 5–6 mixed / outdated /
   > context-dependent · 7–8 misleading / marketing spin / cherry-picked · 9–10 false / clickbait.
   Lead with `**Overall video: [N/10]** — one-line why`. Then one bullet per claim:
   `- **[N/10]** *"quote"* — verdict — one-line evidence ([source](url))`.
   **Write scores as `[N/10]` in square brackets** — the HTML generator renders those as
   colour-coded badges (green ≤3, amber 4–6, red ≥7). Budget: the top ~5–8 checkable claims,
   ~1 search each; skip pure opinion unless it's stated as fact.

Keep it evidence-first and fair: reward true claims with low scores, don't punish a good
video for a clickbait title beyond the title's own bullet.

## Step 4 — Confirm the category (cheap)
Resolve `$VAULT_DIR` — prefer `vault_dir` from `~/.config/yt-video-review-eval/config.toml`, else
`$WATCH_VAULT_DIR`, else `~/Second brain` → `~/Documents/Obsidian` → `~/Obsidian`. Read
`$VAULT_DIR/CLAUDE.md`, sanity-check the analyst's suggested category against its
routing rules, **state the choice in chat** ("Filing under X because …", overridable),
and make sure the report frontmatter's `category:` matches.

## Step 5 — Ingest (obey the vault's own op; text-only, cheap)
`$VAULT_DIR/CLAUDE.md` is authoritative — run its Ingest op exactly. In practice:
slug = slugified title + `-YYYY-MM-DD`; move report + hero frames into
`<CAT>/watched/<slug>/`; append one line to `<CAT>/log.md`; write a polished topic note
`<CAT>/<Title>.md` (strip `|`/`:` from the filename) with the vault's frontmatter, `⚠️`
flags, and `[[wikilinks]]` to siblings. Also carry the research outputs into the note: a
`hype_score:` frontmatter field, a `⚖️` reality-check callout (overall `[N/10]` + the
worst offenders), and a `📥` **Get it** line with the official link + install one-liner —
and append the overall score to the `log.md` line.

## Step 6 — Review HTML (script, 0 tokens) + save in vault
```
python3 <report_to_html.py> "<CAT>/watched/<slug>/report.md"
```
Writes `<CAT>/watched/<slug>/review.html` (self-contained, hero frames embedded,
transcript collapsed). Add `> 🖥️ [Review page](watched/<slug>/review.html)` near the top
of the topic note, then open the HTML with the configured `open_command`
(`open` / `xdg-open` / `explorer.exe`) if `auto_open_review` is on.

## Step 6.5 — Optional Thalix hand-off (default OFF, fail-soft)
After `report.md` is final in the vault, run the guarded hand-off script. It is a **silent
no-op** unless `[thalix].enabled = true` in config AND the `thalix` binary is on PATH, and it
**never** breaks the vault flow (disabled / absent / CLI error / hang all → exit 0):
```
python3 ~/.claude/skills/yt-video-review-eval/scripts/thalix_handoff.py "<CAT>/watched/<slug>/report.md"
```
Do not mention Thalix to the user when it is disabled. Self-check: `thalix_handoff.py --selftest`.

## Step 7 — Report back + clean up
Tell the user: category chosen, topic-note path, `watched/<slug>/` report + review.html
paths, `log.md` line. Then `rm -rf <workdir>`.

## Notes
- Scripts are stdlib-only; self-checks: `report_to_html.py --demo`, `compact_transcript.py`.
- No vault → skip Steps 4–7, keep the workdir, tell the user + suggest `WATCH_VAULT_DIR`.
- The user opted into ingest by invoking this — don't re-ask; only surface the category.
- **Token budget guardrails:** 1 Sonnet sub-agent per video by default; hero+spread frames
  only (cap ~15); Opus only on an explicit escalation flag; everything scriptable stays a script.
