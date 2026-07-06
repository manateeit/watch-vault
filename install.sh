#!/usr/bin/env bash
#
# watch-vault installer.
#   git clone https://github.com/manateeit/watch-vault && cd watch-vault && ./install.sh
# Re-running is safe (idempotent). Installs the watch-vault skill, the upstream `watch`
# engine (MIT, taoufik123-collab/claude-watch) + our cookie patch, checks system deps,
# sets up (or creates) an Obsidian vault, and writes your config.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$ROOT/scripts/lib.sh"

WATCH_UPSTREAM="https://github.com/taoufik123-collab/claude-watch"
SKILLS_DIR="$HOME/.claude/skills"
CFG_DIR="$HOME/.config/watch-vault"
OS="$(detect_os)"
VERSION="$(cat "$ROOT/VERSION" 2>/dev/null || echo 0.0.0)"

printf '\n%s\n' "${BOLD}watch-vault installer${RESET} ${DIM}v$VERSION · $OS${RESET}"
printf '%s\n\n' "${DIM}Turn any video URL into a filed, fact-checked note in your Obsidian vault.${RESET}"

# ── 1. Host + system dependencies ─────────────────────────────────────────────────────────
say "Checking prerequisites…"
have python3 || die "python3 is required (3.10+). Install it and re-run."
[ -d "$SKILLS_DIR" ] || { warn "No $SKILLS_DIR — is Claude Code installed? Creating the dir anyway."; mkdir -p "$SKILLS_DIR"; }
for bin in ffmpeg ffprobe yt-dlp; do
  if have "$bin"; then ok "$bin present"
  else
    warn "$bin missing"
    if ask_yes_no "Install $bin now?" y; then
      case "$bin" in ffmpeg|ffprobe) pkg_install ffmpeg ;; yt-dlp) pkg_install yt-dlp ;; esac
      ok "$bin installed"
    else warn "Skipping $bin — video download/frames will fail until it's installed."; fi
  fi
done

# ── 2. The `watch` engine (upstream MIT dependency) ───────────────────────────────────────
if [ -d "$SKILLS_DIR/watch/scripts" ]; then
  ok "watch engine already installed (reusing yours)"
else
  say "Installing the watch engine from $WATCH_UPSTREAM …"
  tmp="$(mktemp -d)"
  if git clone --depth 1 "$WATCH_UPSTREAM" "$tmp/claude-watch" >/dev/null 2>&1; then
    # locate the skill dir inside the upstream repo (it ships as a plugin/skill)
    engine="$(find "$tmp/claude-watch" -type d -name scripts -path '*watch*' | head -1)"
    engine="${engine%/scripts}"
    [ -n "$engine" ] || engine="$tmp/claude-watch"
    mkdir -p "$SKILLS_DIR/watch"
    cp -R "$engine/." "$SKILLS_DIR/watch/"
    ok "watch engine installed"
  else
    warn "Could not clone the watch engine automatically."
    warn "Install it manually from $WATCH_UPSTREAM into $SKILLS_DIR/watch, then re-run."
  fi
  rm -rf "$tmp"
fi
# our cookie patch (idempotent, non-destructive)
if [ -f "$SKILLS_DIR/watch/scripts/download.py" ]; then
  python3 "$ROOT/scripts/ensure_cookie_support.py" "$SKILLS_DIR/watch/scripts/download.py" || true
fi
# validate the engine deps if its setup exists
[ -f "$SKILLS_DIR/watch/scripts/setup.py" ] && python3 "$SKILLS_DIR/watch/scripts/setup.py" --check >/dev/null 2>&1 && ok "watch engine deps OK" || true

# ── 3. The watch-vault skill ──────────────────────────────────────────────────────────────
say "Installing the watch-vault skill…"
mkdir -p "$SKILLS_DIR/watch-vault"
cp -R "$ROOT/skills/watch-vault/." "$SKILLS_DIR/watch-vault/"
ok "watch-vault skill installed → $SKILLS_DIR/watch-vault"

# ── 4. Vault ──────────────────────────────────────────────────────────────────────────────
say "Locating your Obsidian vault…"
vault=""
for c in "$WATCH_VAULT_DIR" "$HOME/Second brain" "$HOME/Documents/Obsidian" "$HOME/Obsidian"; do
  [ -n "$c" ] && [ -d "$c" ] && { vault="$c"; break; }
done
if [ -n "$vault" ]; then
  ok "Found vault: $vault"
else
  warn "No vault found."
  if ask_yes_no "Create a new vault now?" y; then
    default_vault="$HOME/Second brain"
    vault="$(ask "New vault path" "$default_vault")"
    mkdir -p "$vault/raw/watched"
    ok "Created vault: $vault"
  else
    vault="$(ask "Path to your existing vault (blank = auto-detect at runtime)" "")"
  fi
fi
# drop the ingest-op CLAUDE.md if the vault has none
if [ -n "$vault" ] && [ ! -f "$vault/CLAUDE.md" ]; then
  if ask_yes_no "Add the watch-vault ingest rules (CLAUDE.md) to this vault?" y; then
    cp "$ROOT/templates/vault-CLAUDE.md" "$vault/CLAUDE.md"
    mkdir -p "$vault/raw/watched"
    ok "Added $vault/CLAUDE.md (edit the Categories to taste)"
  fi
elif [ -n "$vault" ]; then
  ok "Vault already has a CLAUDE.md — leaving it untouched."
fi

# ── 5. Optional: Whisper key + YouTube cookies ────────────────────────────────────────────
mkdir -p "$HOME/.config/watch"
env_file="$HOME/.config/watch/.env"; touch "$env_file"; chmod 600 "$env_file"
if ! grep -qE "^(GROQ|OPENAI)_API_KEY=.+" "$env_file" 2>/dev/null; then
  say "Whisper (transcribes videos that have NO captions) is optional."
  if ask_yes_no "Add a Whisper API key now?" n; then
    prov="$(ask "Provider (groq/openai)" groq)"
    key="$(ask "Paste the API key" "")"
    [ -n "$key" ] && { echo "$([ "$prov" = openai ] && echo OPENAI_API_KEY || echo GROQ_API_KEY)=$key" >> "$env_file"; ok "Key saved to $env_file"; }
  fi
fi
cookies="$(ask "Which browser is logged into YouTube? (blank/safari/chrome/firefox — only needed if you hit the bot gate)" "")"

# ── 6. Write config ───────────────────────────────────────────────────────────────────────
mkdir -p "$CFG_DIR"
open_cmd="$(detect_open_cmd)"
cfg="$CFG_DIR/config.toml"
if [ -f "$cfg" ]; then cp "$cfg" "$cfg.bak.$(date +%s 2>/dev/null || echo prev)" 2>/dev/null || true; fi
sed -e "s#^vault_dir = .*#vault_dir = \"$vault\"#" \
    -e "s#^open_command = .*#open_command = \"$open_cmd\"#" \
    -e "s#^cookies_from_browser = .*#cookies_from_browser = \"$cookies\"#" \
    -e "s#^source_dir = .*#source_dir = \"$ROOT\"#" \
    -e "s#^version = .*#version = \"$VERSION\"#" \
    "$ROOT/config.example.toml" > "$cfg"
ok "Wrote $cfg"

# ── 7. Self-check + done ──────────────────────────────────────────────────────────────────
say "Verifying…"
python3 "$SKILLS_DIR/watch-vault/scripts/report_to_html.py" --demo >/dev/null && ok "report_to_html self-check passed"
printf '\n%s\n' "${GREEN}${BOLD}watch-vault installed.${RESET}"
cat <<EOF

  Next steps:
    1. Open Claude Code.
    2. Paste a YouTube URL and say:  ${BOLD}watch-vault <url>${RESET}
    3. Review the note + review.html it files into your vault.

  Config:   $cfg   (edit categories in ${vault:-<your vault>}/CLAUDE.md)
  Update:   ${BOLD}./update.sh${RESET}   ·   Check:  python3 $SKILLS_DIR/watch-vault/scripts/check_updates.py
EOF
