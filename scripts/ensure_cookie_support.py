#!/usr/bin/env python3
"""
Non-destructively add YouTube-cookie passthrough to the upstream `watch` engine's
download.py, so yt-video-review-eval can clear the "confirm you're not a bot" gate via
WATCH_COOKIES_FROM_BROWSER / WATCH_COOKIES_FILE. Idempotent — safe to re-run.

    python ensure_cookie_support.py ~/.claude/skills/watch/scripts/download.py
"""
import sys
from pathlib import Path

MARKER = "WATCH_COOKIES_FROM_BROWSER"

IMPORT_ANCHOR = "import shutil"
IMPORT_ADD = "import os\nimport shutil"

CMD_ANCHOR = '    cmd = [\n        "yt-dlp",\n'
CMD_ADD = (
    '    # [yt-video-review-eval] cookies passthrough for bot-gated networks. Set\n'
    '    # WATCH_COOKIES_FROM_BROWSER=safari|chrome|firefox or WATCH_COOKIES_FILE=cookies.txt\n'
    '    _cb = os.environ.get("WATCH_COOKIES_FROM_BROWSER", "").strip()\n'
    '    _cf = os.environ.get("WATCH_COOKIES_FILE", "").strip()\n'
    '    _cookie_args = (["--cookies-from-browser", _cb] if _cb\n'
    '                    else ["--cookies", _cf] if _cf else [])\n'
    '    cmd = [\n        "yt-dlp",\n        *_cookie_args,\n'
)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: ensure_cookie_support.py <path-to-download.py>")
    p = Path(sys.argv[1])
    if not p.exists():
        sys.exit(f"not found: {p}")
    src = p.read_text()
    if MARKER in src:
        print(f"cookie support already present in {p.name}")
        return
    if CMD_ANCHOR not in src:
        print(f"! could not find the yt-dlp command block in {p.name}; skipping "
              f"(the watch engine layout may have changed). Cookie bypass unavailable.")
        return
    if "import os" not in src.split("def ", 1)[0]:
        src = src.replace(IMPORT_ANCHOR, IMPORT_ADD, 1)
    src = src.replace(CMD_ANCHOR, CMD_ADD, 1)
    p.write_text(src)
    print(f"✓ added cookie passthrough to {p.name}")


if __name__ == "__main__":
    main()
