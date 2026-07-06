#!/usr/bin/env python3
"""
Self-contained updater for yt-video-review-eval. Pulls the latest and reinstalls the skill
in place — works even if the original `git clone` is gone (re-clones to a cache dir).
Invoked by the `yt-video-review-eval update` subcommand. Stdlib only (shells out to git).

    python self_update.py           # update to latest main
    python self_update.py --dry-run # show what it would do
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path

CFG = Path.home() / ".config" / "yt-video-review-eval" / "config.toml"
SKILL_DIR = Path.home() / ".claude" / "skills" / "yt-video-review-eval"
WATCH_DL = Path.home() / ".claude" / "skills" / "watch" / "scripts" / "download.py"
CACHE = Path.home() / ".local" / "share" / "yt-video-review-eval" / "src"
DEFAULT_REPO = "manateeit/yt-video-review-eval"


def read_cfg():
    cfg = {}
    if CFG.exists():
        for line in CFG.read_text().splitlines():
            m = re.match(r'^\s*([a-z_]+)\s*=\s*"?([^"#]*)"?', line)
            if m:
                cfg[m.group(1)] = m.group(2).strip()
    return cfg


def git(*args):
    subprocess.run(["git", *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_source(cfg, dry):
    """Return a path to an up-to-date repo checkout."""
    src = cfg.get("source_dir", "")
    if src and (Path(src) / ".git").exists():
        if dry:
            return Path(src)
        try:
            git("-C", src, "pull", "--ff-only")
            return Path(src)
        except subprocess.CalledProcessError:
            print("! pull failed on the recorded checkout; using a fresh clone.")
    repo = cfg.get("repo") or DEFAULT_REPO
    url = f"https://github.com/{repo}"
    if dry:
        print(f"would clone/pull {url} -> {CACHE}")
        return CACHE
    if (CACHE / ".git").exists():
        git("-C", str(CACHE), "pull", "--ff-only")
    else:
        if CACHE.exists():
            shutil.rmtree(CACHE)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--depth", "1", url, str(CACHE))
    return CACHE


def copytree(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        target = dst / p.relative_to(src)
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(p, target)


def set_cfg(key, val):
    if not CFG.exists():
        return
    txt = CFG.read_text()
    if re.search(rf'^{key} = .*$', txt, flags=re.M):
        txt = re.sub(rf'^{key} = .*$', f'{key} = "{val}"', txt, flags=re.M)
        CFG.write_text(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if shutil.which("git") is None:
        sys.exit("git is required to update yt-video-review-eval.")

    cfg = read_cfg()
    old = cfg.get("version", "?")
    src = ensure_source(cfg, args.dry_run)
    new = (src / "VERSION").read_text().strip() if (src / "VERSION").exists() else "?"

    if args.dry_run:
        print(f"dry-run: {old} -> {new} (would reinstall skill from {src})")
        return

    copytree(src / "skills" / "yt-video-review-eval", SKILL_DIR)
    patcher = src / "scripts" / "ensure_cookie_support.py"
    if WATCH_DL.exists() and patcher.exists():
        subprocess.run([sys.executable, str(patcher), str(WATCH_DL)], check=False)
    set_cfg("version", new)
    set_cfg("source_dir", str(src))
    subprocess.run([sys.executable, str(SKILL_DIR / "scripts" / "report_to_html.py"), "--demo"],
                   check=False, stdout=subprocess.DEVNULL)

    if old == new:
        print(f"✓ yt-video-review-eval reinstalled; already at latest ({new}).")
    else:
        print(f"✓ yt-video-review-eval updated {old} -> {new}. Restart Claude Code to pick up SKILL.md changes.")


if __name__ == "__main__":
    main()
