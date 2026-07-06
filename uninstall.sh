#!/usr/bin/env bash
# Remove the watch-vault skill and config. Never touches your vault or its notes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$ROOT/scripts/lib.sh"

SKILLS_DIR="$HOME/.claude/skills"

rm -rf "$SKILLS_DIR/watch-vault" && ok "Removed $SKILLS_DIR/watch-vault"
if ask_yes_no "Also remove config (~/.config/watch-vault)?" n; then
  rm -rf "$HOME/.config/watch-vault" && ok "Removed config"
fi
if [ -d "$SKILLS_DIR/watch" ] && ask_yes_no "Also remove the watch engine (~/.claude/skills/watch)?" n; then
  rm -rf "$SKILLS_DIR/watch" && ok "Removed watch engine"
fi
say "Your vault and its notes were left untouched."
