#!/usr/bin/env python3
"""
Collapse a /watch report's rolling-caption transcript into compact ~30s
paragraphs, so it's cheap to read in full. Stdlib only.

    python compact_transcript.py path/to/report.md          # -> prints paras
    python compact_transcript.py report.md --bucket 45 --out paras.txt
"""
import argparse, re, sys
from pathlib import Path


def to_s(ts):
    p = [int(x) for x in ts.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def fmt(s):
    h, m, ss = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{ss:02d}" if h else f"{m}:{ss:02d}"


def compact(text, bucket=30):
    cap = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
    rows = []
    for ln in text.splitlines():
        m = cap.match(ln)
        if m:
            rows.append((m.group(1), m.group(2).strip()))
    # rolling-caption dedupe: keep only the new words each line adds
    out, prev = [], []
    for ts, t in rows:
        w = t.split()
        new = w
        for k in range(min(len(prev), len(w)), 0, -1):
            if prev[-k:] == w[:k]:
                new = w[k:]
                break
        if new:
            out.append((to_s(ts), " ".join(new)))
        prev = w
    # bucket into paragraphs
    paras, cur, start = [], [], None
    for s, t in out:
        if start is None:
            start = s
        if s - start >= bucket and cur:
            paras.append((start, " ".join(cur)))
            cur, start = [], s
        cur.append(t)
    if cur:
        paras.append((start, " ".join(cur)))
    return "\n\n".join(f"[{fmt(s)}] {t}" for s, t in paras if t.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report")
    ap.add_argument("--bucket", type=int, default=30)
    ap.add_argument("--out")
    args = ap.parse_args()
    text = Path(args.report).read_text(encoding="utf-8")
    result = compact(text, args.bucket)
    if args.out:
        Path(args.out).write_text(result + "\n", encoding="utf-8")
        print(f"{args.out} ({result.count(chr(10) + chr(10)) + 1} paragraphs)")
    else:
        print(result)


if __name__ == "__main__":
    main()
