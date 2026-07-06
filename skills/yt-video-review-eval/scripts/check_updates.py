#!/usr/bin/env python3
"""
Check whether a newer yt-video-review-eval release exists on GitHub. Stdlib only.

Compares the local VERSION (installed) against the latest git tag / release of the
configured repo. Prints a one-line status and exits 0 (up to date / unknown) or
10 (update available) so shells/CI can branch on it.

    python check_updates.py                 # uses ~/.config/yt-video-review-eval/config.toml
    python check_updates.py --repo owner/name --local 0.1.0
"""
import argparse, json, os, re, sys, urllib.request
from pathlib import Path

CONFIG = Path.home() / ".config" / "yt-video-review-eval" / "config.toml"


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
    req = urllib.request.Request(url, headers={"User-Agent": "yt-video-review-eval-updater"})
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
        print("yt-video-review-eval: repo not configured; cannot check for updates.")
        return 0
    if not local:
        print("yt-video-review-eval: local version unknown; run the installer.")
        return 0
    try:
        remote = latest_tag(repo)
    except Exception as exc:  # offline / rate-limited / no tags
        print(f"yt-video-review-eval: update check skipped ({exc}).")
        return 0
    if not remote:
        print(f"yt-video-review-eval {local}: no releases published yet on {repo}.")
        return 0
    if norm(remote) > norm(local):
        print(f"yt-video-review-eval: update available — {local} → {remote}. Run: yt-video-review-eval update")
        return 10
    print(f"yt-video-review-eval {local}: up to date (latest {remote}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
