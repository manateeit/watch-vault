#!/usr/bin/env python3
"""Optional, default-OFF hand-off of a finished report.md to the Thalix substrate.

The real ingest entry point is the FR-009 verb run from the Thalix repo root:

    python3 -m ingest "<report.md>" --kind video_review --scope <scope>

(NOT `thalix ingest` — that CLI subcommand does not exist; the `thalix` binary is
read-only: search/get/atoms/propose/...). This script fires ONLY when BOTH are true:
  1. [thalix].enabled = true in ~/.config/yt-video-review-eval/config.toml
     (or WATCH_VAULT_THALIX_ENABLED=1 in the env), AND
  2. the Thalix repo (with its `ingest` module) exists at [thalix].repo_dir.
Otherwise it is a silent no-op. Every failure axis — disabled, repo absent, ingest
error, or a hung run (Python-native timeout) — is swallowed to at most one stderr
line and exits 0, so the vault flow is never broken.

stdlib only. Usage:  python3 thalix_handoff.py "<CAT>/watched/<slug>/report.md"
Self-check:          python3 thalix_handoff.py --selftest
"""
import os
import subprocess
import sys
from pathlib import Path

CONFIG = Path.home() / ".config" / "yt-video-review-eval" / "config.toml"
DEFAULT_REPO_DIR = str(Path.home() / "development" / "thalix")


def _read_thalix_section(text):
    """Minimal TOML-subset read of the [thalix] table. stdlib-only, version-proof
    (avoids tomllib so it runs on pre-3.11 pythons). Returns a dict of raw strings."""
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
    cfg = {"enabled": False, "scope": "dev", "timeout_seconds": 30,
           "repo_dir": DEFAULT_REPO_DIR}
    if CONFIG.exists():
        raw = _read_thalix_section(CONFIG.read_text())
        if "enabled" in raw:
            cfg["enabled"] = raw["enabled"].lower() == "true"
        if raw.get("scope"):
            cfg["scope"] = raw["scope"]
        if raw.get("timeout_seconds", "").isdigit():
            cfg["timeout_seconds"] = int(raw["timeout_seconds"])
        if raw.get("repo_dir"):
            cfg["repo_dir"] = str(Path(raw["repo_dir"]).expanduser())
    env = os.environ.get("WATCH_VAULT_THALIX_ENABLED")
    if env is not None:
        cfg["enabled"] = env.strip() in ("1", "true", "True")
    return cfg


def handoff(report_path, cfg):
    """Returns a short status string; never raises."""
    if not cfg["enabled"]:
        return "disabled"
    repo = Path(cfg["repo_dir"])
    if not (repo / "ingest" / "__main__.py").is_file():
        return "no-ingest"          # Thalix repo/ingest module not present here
    if not Path(report_path).is_file():
        return "no-report"
    try:
        subprocess.run(
            [sys.executable, "-m", "ingest", report_path,
             "--kind", "video_review", "--scope", cfg["scope"]],
            cwd=str(repo),
            timeout=cfg["timeout_seconds"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        return "ingested"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception:               # ingest error, scope not resolvable, anything — fail soft
        return "error"


def _selftest():
    sample = ('[other]\nx = 1\n[thalix]\nenabled = true  # inline comment\n'
              'scope = "aws"\ntimeout_seconds = 5\nrepo_dir = "/tmp/nope"\n')
    got = _read_thalix_section(sample)
    assert got["enabled"] == "true", got
    assert got["scope"] == "aws", got
    assert got["repo_dir"] == "/tmp/nope", got
    # disabled -> no-op regardless of repo
    assert handoff("/nonexistent", {"enabled": False, "scope": "dev",
                                    "timeout_seconds": 1, "repo_dir": "/tmp"}) == "disabled"
    # enabled but no ingest module at repo_dir -> fail-soft, NOT treated as ingested
    assert handoff("/nonexistent", {"enabled": True, "scope": "dev",
                                    "timeout_seconds": 1, "repo_dir": "/tmp/definitely-not-thalix"}) == "no-ingest"
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) != 2:
        print("usage: thalix_handoff.py <report.md path> | --selftest", file=sys.stderr)
        sys.exit(0)
    status = handoff(sys.argv[1], load_config())
    if status not in ("disabled", "ingested"):
        print(f"[thalix] hand-off {status} — vault unaffected", file=sys.stderr)
    sys.exit(0)  # ALWAYS 0: the vault flow must never fail because of this
