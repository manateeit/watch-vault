#!/usr/bin/env bash
# Pull the latest watch-vault and re-install the skill in place (non-interactive).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$ROOT/scripts/lib.sh"

SKILLS_DIR="$HOME/.claude/skills"
CFG="$HOME/.config/watch-vault/config.toml"

# Prefer the source dir recorded at install time; fall back to this checkout.
src="$ROOT"
[ -f "$CFG" ] && src="$(sed -n 's/^source_dir = "\(.*\)"/\1/p' "$CFG" | head -1)"
[ -d "$src/.git" ] || src="$ROOT"

say "Updating from $src …"
if [ -d "$src/.git" ]; then
  before="$(git -C "$src" rev-parse --short HEAD 2>/dev/null || echo '?')"
  git -C "$src" pull --ff-only || warn "git pull failed — continuing with current checkout."
  after="$(git -C "$src" rev-parse --short HEAD 2>/dev/null || echo '?')"
  [ "$before" = "$after" ] && ok "Already at latest ($after)" || ok "Updated $before → $after"
fi

say "Re-installing the watch-vault skill…"
mkdir -p "$SKILLS_DIR/watch-vault"
cp -R "$src/skills/watch-vault/." "$SKILLS_DIR/watch-vault/"
[ -f "$SKILLS_DIR/watch/scripts/download.py" ] && \
  python3 "$src/scripts/ensure_cookie_support.py" "$SKILLS_DIR/watch/scripts/download.py" || true

# refresh version in config
if [ -f "$CFG" ]; then
  ver="$(cat "$src/VERSION" 2>/dev/null || echo 0.0.0)"
  sed -i.bak "s#^version = .*#version = \"$ver\"#" "$CFG" && rm -f "$CFG.bak"
fi
python3 "$SKILLS_DIR/watch-vault/scripts/report_to_html.py" --demo >/dev/null && ok "self-check passed"
ok "watch-vault updated."
