#!/usr/bin/env python3
"""
Check whether a newer watch-vault release exists on GitHub. Stdlib only.

Compares the local VERSION (installed) against the latest git tag / release of the
configured repo. Prints a one-line status and exits 0 (up to date / unknown) or
10 (update available) so shells/CI can branch on it.

    python check_updates.py                 # uses ~/.config/watch-vault/config.toml
    python check_updates.py --repo owner/name --local 0.1.0
"""
import argparse, json, os, re, sys, urllib.request
from pathlib import Path

CONFIG = Path.home() / ".config" / "watch-vault" / "config.toml"


def read_config():
    cfg = {}
    if CONFIG.exists():
        for line in CONFIG.read_text().splitlines():
            m = re.match(r'^\s*([a-z_]+)\s*=\s*"?([^"#]*)"?', line)
            if m:
                cfg[m.group(1)] = m.group(2).strip()
    return cfg


def norm(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3] or [0])


def latest_tag(repo):
    url = f"https://api.github.com/repos/{repo}/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "watch-vault-updater"})
    with urllib.request.urlopen(req, timeout=10) as r:
        tags = json.load(r)
    return tags[0]["name"] if tags else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo")
    ap.add_argument("--local")
    args = ap.parse_args()
    cfg = read_config()
    repo = args.repo or cfg.get("repo")
    local = args.local or cfg.get("version") or (
        (Path(cfg.get("source_dir", "")) / "VERSION").read_text().strip()
        if cfg.get("source_dir") and (Path(cfg["source_dir"]) / "VERSION").exists() else None)

    if not repo:
        print("watch-vault: repo not configured; cannot check for updates.")
        return 0
    if not local:
        print("watch-vault: local version unknown; run the installer.")
        return 0
    try:
        remote = latest_tag(repo)
    except Exception as exc:  # offline / rate-limited / no tags
        print(f"watch-vault: update check skipped ({exc}).")
        return 0
    if not remote:
        print(f"watch-vault {local}: no releases published yet on {repo}.")
        return 0
    if norm(remote) > norm(local):
        print(f"watch-vault: update available — {local} → {remote}. Run: watch-vault update")
        return 10
    print(f"watch-vault {local}: up to date (latest {remote}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
