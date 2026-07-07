#!/usr/bin/env python3
"""Optional, default-OFF hand-off of a finished report.md to a local `thalix` CLI.

Fires ONLY when BOTH are true:
  1. [thalix].enabled = true in ~/.config/yt-video-review-eval/config.toml
     (or WATCH_VAULT_THALIX_ENABLED=1 in the env), AND
  2. the `thalix` binary is on PATH.
Otherwise it is a silent no-op. Every failure axis — disabled, absent, CLI error,
or a hung CLI (Python-native timeout, no dependency on the `timeout` binary) — is
swallowed to at most one stderr line and exits 0, so the vault flow is never broken.

stdlib only. Usage:  python3 thalix_handoff.py "<CAT>/watched/<slug>/report.md"
Self-check:          python3 thalix_handoff.py --selftest
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = Path.home() / ".config" / "yt-video-review-eval" / "config.toml"


def _read_thalix_section(text):
    """Minimal TOML-subset read of the [thalix] table. stdlib-only, version-proof
    (avoids tomllib so it runs on pre-3.11 pythons). Returns a dict of raw string values."""
    out, in_section = {}, False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_section = line == "[thalix]"
            continue
        if in_section and "=" in line:
            key, val = line.split("=", 1)
            out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def load_config():
    cfg = {"enabled": False, "scope": "dev", "timeout_seconds": 10}
    if CONFIG.exists():
        raw = _read_thalix_section(CONFIG.read_text())
        if "enabled" in raw:
            cfg["enabled"] = raw["enabled"].lower() == "true"
        if raw.get("scope"):
            cfg["scope"] = raw["scope"]
        if raw.get("timeout_seconds", "").isdigit():
            cfg["timeout_seconds"] = int(raw["timeout_seconds"])
    # env override wins over the file
    env = os.environ.get("WATCH_VAULT_THALIX_ENABLED")
    if env is not None:
        cfg["enabled"] = env.strip() in ("1", "true", "True")
    return cfg


def handoff(report_path, cfg):
    """Returns a short status string; never raises."""
    if not cfg["enabled"]:
        return "disabled"
    if shutil.which("thalix") is None:
        return "absent"
    if not Path(report_path).is_file():
        return "no-report"
    try:
        subprocess.run(
            ["thalix", "ingest", report_path,
             "--kind", "video_review", "--scope", cfg["scope"]],
            timeout=cfg["timeout_seconds"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        return "ingested"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception:  # CLI error, permissions, anything — fail soft
        return "error"


def _selftest():
    # config parsing
    sample = '[other]\nx = 1\n[thalix]\nenabled = true  # inline comment\nscope = "aws"\ntimeout_seconds = 5\n'
    got = _read_thalix_section(sample)
    assert got["enabled"] == "true", got
    assert got["scope"] == "aws", got
    assert got["timeout_seconds"] == "5", got
    # disabled -> no-op regardless of binary
    assert handoff("/nonexistent", {"enabled": False, "scope": "dev", "timeout_seconds": 1}) == "disabled"
    # enabled but binary absent must NOT be treated as ingested (fail-soft path)
    if shutil.which("thalix") is None:
        assert handoff("/nonexistent", {"enabled": True, "scope": "dev", "timeout_seconds": 1}) == "absent"
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) != 2:
        print("usage: thalix_handoff.py <report.md path> | --selftest", file=sys.stderr)
        sys.exit(0)  # not an error worth breaking the vault flow over
    status = handoff(sys.argv[1], load_config())
    if status not in ("disabled", "ingested"):
        print(f"[thalix] hand-off {status} — vault unaffected", file=sys.stderr)
    sys.exit(0)  # ALWAYS 0: the vault flow must never fail because of this
