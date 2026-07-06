# watch-vault

**Give it a YouTube URL. Get a filed, fact-checked note in your Obsidian vault — with a review page.**

watch-vault is a workflow for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Hand it a
video link and it will:

1. **Watch** the video (frames + transcript, via the [`watch`](https://github.com/taoufik123-collab/claude-watch) engine).
2. **Auto-pick the category** it belongs in, using *your* vault's rules.
3. **Find how to get** any software/links the video mentions (official site, install steps, docs).
4. **Reality-check** its claims on a **1–10 hype scale** (1 = true, 10 = hype), sourced from the web.
5. **Ingest** it into your vault: a polished topic note + raw report + hero frames + a log entry.
6. **Generate a review HTML page** (with colour-coded hype badges) and open it.

It's built for **token discipline**: the expensive frame-vision and web research run in **sub-agents**
(Sonnet), so images and fetched pages never bloat your main conversation; Opus is used only when a
video is genuinely hard.

> **Why?** YouTube is full of hype. watch-vault turns videos into durable, *scored* notes so your
> second brain accumulates signal, not clickbait.

---

## Requirements

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (this workflow runs inside it).
- **macOS, Linux, or WSL.**
- System tools (the installer offers to install them): `python3` (3.10+), `ffmpeg`, `ffprobe`, `yt-dlp`.
- **No pip packages** — all scripts are stdlib-only.
- Optional: an [Obsidian](https://obsidian.md) vault (the installer can create one), and a Groq/OpenAI
  key for videos that have no captions.

## Install

```bash
git clone https://github.com/manateeit/watch-vault
cd watch-vault
./install.sh
```

The installer is idempotent and walks you through: system deps → the `watch` engine (fetched from
upstream) → the watch-vault skill → finding **or creating** your vault → optional Whisper key and
YouTube-cookies browser → writing your config. Then restart Claude Code.

<sub>One-liner (reviews the script first is recommended): `git clone https://github.com/manateeit/watch-vault && cd watch-vault && ./install.sh`</sub>

## Use

In Claude Code, paste a URL and say **`watch-vault <url>`** (or "watch and ingest this", or just paste
the URL). That's it. You'll get, in your vault:

```
<Category>/
├── <Title>.md                       ← polished topic note (TL;DR, ⚖️ reality-check, 📥 get-it, sections)
├── log.md                           ← one-line running index (with hype score)
└── watched/<slug>/
    ├── report.md                    ← full report + transcript + Resources + Reality-check
    ├── review.html                  ← self-contained review page (hero frames + hype badges)
    └── frame_*.jpg                  ← hero frames
```

## Configuration

Everything a new user might need to set lives in **`~/.config/watch-vault/config.toml`** (created by
the installer; copy of [`config.example.toml`](config.example.toml)). Any value can be overridden by an
env var `WATCH_VAULT_<NAME>`.

| Setting | What it does | Default |
|---|---|---|
| `vault_dir` | Absolute path to your Obsidian vault | auto-detect |
| **Vault `CLAUDE.md`** | **The category list + ingest rules** — the main thing you customize (see below) | template installed |
| `open_command` | How review.html is opened (`open` / `xdg-open` / `explorer.exe`) | per-OS |
| `auto_open_review` | Open the review page after each run | `true` |
| `cookies_from_browser` | Browser logged into YouTube — only needed if you hit the bot gate | `""` |
| Whisper key | `GROQ_API_KEY`/`OPENAI_API_KEY` in `~/.config/watch/.env`, for caption-less videos | none |
| `whisper_backend` | `auto` / `groq` / `openai` / `none` | `auto` |
| `routing_posture` | Cost/quality: `balanced` / `aggressive` / `quality` | `balanced` |
| `max_frames` | Hard cap on frames the analyst reads (token control) | `15` |
| `reality_check` | Run the 1–10 hype reality-check stage | `true` |
| `resource_finder` | Research how to get mentioned software/links | `true` |

### Your vault's categories (`<vault>/CLAUDE.md`)

This is the file that makes ingest *yours*. It defines your category folders and the ingest op.
The installer drops a [template](templates/vault-CLAUDE.md) with `AI/ Finance/ Health/ Learning/` —
**edit the Categories table** to match how you think. watch-vault reads it every run and files
accordingly (and always tells you the pick so you can redirect it).

### Routing / cost

The **Balanced** default: a **Sonnet** sub-agent does all frame-reading + report writing (so image
tokens stay out of your main thread), **Haiku** labels the category, and **Opus** is spawned to audit
only when the analyst flags `confidence: low` or the video is `>30 min AND dense`. Deterministic steps
(download, frames, transcript, HTML) are plain scripts — **zero tokens**. Switch `routing_posture` to
`aggressive` (cheaper) or `quality` (Opus on anything long/high-stakes).

## Updating

```bash
python3 skills/watch-vault/scripts/check_updates.py   # or: make check-updates
./update.sh                                            # or: make update
```
`check_updates.py` compares your installed `VERSION` to the latest GitHub tag; `update.sh` pulls and
re-installs the skill in place.

## Uninstall

```bash
./uninstall.sh
```
Removes the skill (and optionally config / the `watch` engine). **Never touches your vault or notes.**

## How it works

```
URL ──▶ watch.py (download+frames+transcript, script) ──▶ report.md
        │
        ├─▶ watch-analyst sub-agent (Sonnet, vision)  ── fills report.md, suggests category
        ├─▶ watch-researcher sub-agent (Sonnet, web)  ── appends Resources + 1–10 Reality-check
        ├─▶ [watch-reviewer sub-agent (Opus)]          ── only on low-confidence / long+dense
        │
        └─▶ ingest (your vault's CLAUDE.md op) ──▶ report_to_html.py ──▶ review.html ──▶ open
```
Full step-by-step spec: [`skills/watch-vault/SKILL.md`](skills/watch-vault/SKILL.md).

## The `watch` engine dependency

The video-watching itself is done by **[`watch`](https://github.com/taoufik123-collab/claude-watch)**
(MIT, © taoufik). watch-vault **does not bundle it** — the installer fetches it from upstream (or reuses
your existing copy) and applies a small, non-destructive cookie patch. Credit to taoufik for the engine.

## Contributing & roadmap

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`ROADMAP.md`](ROADMAP.md). Issues and PRs welcome.

## License

[MIT](LICENSE) © Chris McKenna. The `watch` engine is separately MIT-licensed by its author.
