#!/usr/bin/env bash
# Fast, dependency-free smoke tests: the stdlib script self-checks + a syntax pass.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S="$ROOT/skills/watch-vault/scripts"
fail=0

check() { printf '  %-38s' "$1"; shift; if "$@" >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; fail=1; fi; }

echo "watch-vault tests"
check "report_to_html --demo"      python3 "$S/report_to_html.py" --demo
check "compact_transcript importable" python3 -c "import ast,sys; ast.parse(open('$S/compact_transcript.py').read())"
check "check_updates importable"   python3 -c "import ast,sys; ast.parse(open('$S/check_updates.py').read())"
check "ensure_cookie_support parse" python3 -c "import ast; ast.parse(open('$ROOT/scripts/ensure_cookie_support.py').read())"
check "install.sh syntax"          bash -n "$ROOT/install.sh"
check "update.sh syntax"           bash -n "$ROOT/update.sh"
check "uninstall.sh syntax"        bash -n "$ROOT/uninstall.sh"
check "lib.sh syntax"              bash -n "$ROOT/scripts/lib.sh"

[ "$fail" = 0 ] && echo "All tests passed." || { echo "Some tests FAILED."; exit 1; }
