#!/usr/bin/env bash
# Remove the yt-video-review-eval skill and config. Never touches your vault or its notes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$ROOT/scripts/lib.sh"

SKILLS_DIR="$HOME/.claude/skills"

rm -rf "$SKILLS_DIR/yt-video-review-eval" && ok "Removed $SKILLS_DIR/yt-video-review-eval"
if ask_yes_no "Also remove config (~/.config/yt-video-review-eval)?" n; then
  rm -rf "$HOME/.config/yt-video-review-eval" && ok "Removed config"
fi
if [ -d "$SKILLS_DIR/watch" ] && ask_yes_no "Also remove the watch engine (~/.claude/skills/watch)?" n; then
  rm -rf "$SKILLS_DIR/watch" && ok "Removed watch engine"
fi
say "Your vault and its notes were left untouched."
