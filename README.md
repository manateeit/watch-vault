# yt-video-review-eval

Batch YouTube video ingest into Obsidian: download, analyze, research, reality-check, and generate HTML reviews.

## Quick Start

**Single video:**
```bash
yt-video-review-eval https://youtu.be/...
```

**Batch (Workflow):**
```
/yt-video-review-eval ["url1", "url2", ...]
```

## Features

- 🎬 Download videos with captions (yt-dlp)
- 🧠 AI analysis: extract title, creator, category, summary
- 🔍 Web research: find official links for mentioned tools/software
- ⚖️ Reality-check: fact-check claims on 1–10 hype scale
- 📁 Auto-route to vault category (AI, Stock Trading)
- 🎨 Self-contained HTML reviews with color-coded hype badges
- ⚡ Sonnet sub-agents handle frames/research (no bloat in main context)

## Installation

```bash
npm install -g claude-code-cli  # if not already installed
claude-code-cli skills add yt-video-review-eval
```

## Usage

### Single URL (Procedural)
```bash
yt-video-review-eval https://youtu.be/iTY8Q449YNQ
```
Follows SKILL.md steps sequentially. Report and HTML saved to vault.

### Batch URLs (Workflow)
```
/yt-video-review-eval ["url1", "url2", "url3"]
```
Runs as Claude Code Workflow with 5 parallel phases. Monitor via `/workflows` dashboard.

## Vault Integration

Videos are routed to your Obsidian vault:
- **AI/**: AI agents, Claude Code, tools, workflows
- **Stock Trading/**: Crypto, trading automation, futures
- Each gets a topic note + watched/video-slug/ report folder + review.html

Configure vault path in `~/.config/yt-video-review-eval/config.toml`.

## Hype Scoring

Reality-check scores rendered as color-coded badges:
- **[1–3]/10**: Green (true)
- **[4–6]/10**: Amber (mixed)
- **[7–10]/10**: Red (hype/false)

## Release History

- **v1.0.0**: Proper Claude Code Workflow implementation, renamed to yt-video-review-eval
- **v0.3.1**: Workflow foundation
- **v0.2.4**: Multi-agent analysis & research pipeline
- **v0.1.0**: Initial release

## License

MIT
