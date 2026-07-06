#!/usr/bin/env python3
"""
Render a filled /watch report.md into a self-contained, theme-aware review.html.

- Embeds hero frames (from the report frontmatter, found next to report.md) as
  base64 data URIs, so the HTML is portable inside the Obsidian vault.
- Renders TL;DR, key moments, hook, editorial, quotes, entities, concepts; the
  transcript goes into a collapsed <details>. The bulky "All frames" list is dropped.
- Stdlib only.

    python report_to_html.py path/to/report.md               # -> review.html next to it
    python report_to_html.py report.md --out review.html --open
    python report_to_html.py --demo
"""
import argparse, base64, html, mimetypes, re, sys
from pathlib import Path


# ---------- parsing ----------

def split_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            return fm, body
    return "", text


def parse_fm(fm):
    meta = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            val = m.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            meta[m.group(1)] = val
    if "hero_frames" in meta:
        raw = meta["hero_frames"].strip().lstrip("[").rstrip("]")
        meta["hero_frames"] = [f.strip() for f in raw.split(",") if f.strip()]
    return meta


def split_sections(body):
    """Return [(title, content)]; content before the first ## goes under ''. """
    out, title, buf = [], "", []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.*)$", line)
        if h:
            out.append((title, "\n".join(buf).strip()))
            title, buf = h.group(1).strip(), []
        else:
            buf.append(line)
    out.append((title, "\n".join(buf).strip()))
    return [(t, c) for t, c in out if c or t]


# ---------- inline + block markdown (minimal) ----------

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[\[([^\]]+)\]\]", r'<span class="wl">\1</span>', s)          # [[wikilink]]
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)          # [t](url)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)                  # **bold**
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)                            # `code`
    s = re.sub(r"(?<![*])\*(?!\s)([^*]+?)\*(?![*])", r"<em>\1</em>", s)        # *em*
    return s


def render_md(md):
    lines = md.splitlines()
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        h = re.match(r"^###\s+(.*)$", ln)
        if h:
            out.append(f"<h4>{inline(h.group(1))}</h4>")
            i += 1
            continue
        if ln.lstrip().startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith(("- ", "* ")):
                item = lines[i].lstrip()[2:]
                cb = re.match(r"^\[([ xX])\]\s*(.*)$", item)
                if cb:
                    box = "checked" if cb.group(1).lower() == "x" else ""
                    items.append(f'<li><input type="checkbox" disabled {box}> {inline(cb.group(2))}</li>')
                else:
                    items.append(f"<li>{inline(item)}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if ln.lstrip().startswith(">"):
            quote = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(("- ", "* ", ">", "###")):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def data_uri(path):
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


# ---------- html ----------

CSS = """
:root{--bg:#f6f7f5;--panel:#fff;--ink:#191a17;--muted:#5a5f57;--line:#e5e6e0;
--accent:#3f6f52;--soft:#e9f1ec;--code:#eef0ec;--chip:#eceee7}
@media(prefers-color-scheme:dark){:root{--bg:#141510;--panel:#1d1e18;--ink:#ecefe6;
--muted:#a3a89c;--line:#2f312a;--accent:#7fc99a;--soft:#1a231a;--code:#131410;--chip:#25271f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:940px;margin:0 auto;padding:0 22px}
header{padding:46px 0 26px;border-bottom:1px solid var(--line)}
.kick{color:var(--accent);font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:12px}
h1{font-size:32px;line-height:1.18;margin:10px 0 12px;letter-spacing:-.02em}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.chip{background:var(--chip);color:var(--muted);font-size:12.5px;padding:3px 10px;border-radius:999px}
.chip a{color:var(--accent);text-decoration:none}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:22px 0 6px}
.gallery img{width:100%;border-radius:10px;border:1px solid var(--line);display:block}
section{padding:26px 0;border-bottom:1px solid var(--line)}
h2{font-size:22px;margin:0 0 8px;letter-spacing:-.01em}
h4{font-size:16px;margin:18px 0 4px}
p{margin:9px 0} ul{margin:9px 0;padding-left:22px} li{margin:5px 0}
a{color:var(--accent)} code{background:var(--code);padding:.12em .4em;border-radius:5px;font-size:.86em;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.wl{color:var(--accent);font-weight:600}
blockquote{margin:12px 0;padding:10px 16px;border-left:3px solid var(--accent);background:var(--soft);border-radius:0 10px 10px 0}
li input{margin-right:6px}
details{margin:26px 0}
summary{cursor:pointer;font-weight:700;font-size:15px;color:var(--muted)}
pre{background:var(--code);border:1px solid var(--line);border-radius:12px;padding:14px 16px;overflow-x:auto;
font-size:12.5px;line-height:1.5;white-space:pre-wrap;margin-top:12px}
footer{padding:26px 0 60px;color:var(--muted);font-size:13px}
.score{display:inline-block;font-weight:800;padding:1px 8px;border-radius:6px;font-size:12.5px;white-space:nowrap}
.s-lo{background:color-mix(in srgb,#2f8f5b 22%,transparent);color:#2f8f5b}
.s-mid{background:color-mix(in srgb,#c9962b 26%,transparent);color:#a37b1f}
.s-hi{background:color-mix(in srgb,#d1493a 22%,transparent);color:#c0392b}
@media(prefers-color-scheme:dark){.s-lo{color:#7fc99a}.s-mid{color:#e2bf5c}.s-hi{color:#f0897a}}
"""

SKIP_SECTIONS = {"all frames"}


def score_pill(n):
    n = int(n)
    cls = "s-lo" if n <= 3 else ("s-mid" if n <= 6 else "s-hi")
    return f'<span class="score {cls}">{n}/10</span>'


def build_html(report_path):
    text = Path(report_path).read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    meta = parse_fm(fm)
    base = Path(report_path).parent
    title = meta.get("title", Path(report_path).stem)

    chips = []
    if meta.get("creator"):
        chips.append(f'<span class="chip">👤 {html.escape(meta["creator"])}</span>')
    if meta.get("duration"):
        chips.append(f'<span class="chip">⏱ {html.escape(meta["duration"])}</span>')
    if meta.get("category"):
        chips.append(f'<span class="chip">🗂 {html.escape(meta["category"])}</span>')
    if meta.get("watched"):
        chips.append(f'<span class="chip">📅 {html.escape(meta["watched"])}</span>')
    if meta.get("source"):
        src = html.escape(meta["source"])
        chips.append(f'<span class="chip"><a href="{src}">▶ source</a></span>')

    imgs = []
    for fn in meta.get("hero_frames", []):
        p = base / fn
        if p.exists():
            imgs.append(f'<img alt="{html.escape(fn)}" src="{data_uri(p)}">')
    gallery = f'<div class="gallery">{"".join(imgs)}</div>' if imgs else ""

    parts = []
    for stitle, content in split_sections(body):
        low = stitle.lower()
        if low in SKIP_SECTIONS or not stitle:
            continue
        if low.startswith("transcript"):
            tx = re.sub(r"^```.*?$", "", content, flags=re.M).strip()
            tx = re.sub(r"_Source:.*?_", "", tx).strip()
            parts.append(
                f"<details><summary>▸ {html.escape(stitle)} (click to expand)</summary>"
                f"<pre>{html.escape(tx)}</pre></details>")
        else:
            rendered = render_md(content)
            if "reality check" in low or "hype" in low:
                rendered = re.sub(r"\[(\d{1,2})/10\]",
                                  lambda m: score_pill(m.group(1)), rendered)
            parts.append(f"<section><h2>{html.escape(stitle)}</h2>{rendered}</section>")

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<header><div class="wrap"><div class="kick">/watch review · vault ingest</div>
<h1>{html.escape(title)}</h1><div class="meta">{''.join(chips)}</div>{gallery}</div></header>
<main class="wrap">{''.join(parts)}</main>
<footer class="wrap">Generated by yt-video-review-eval from report.md · lives beside the raw report in your vault.</footer>
</body></html>"""


def demo():
    sample = ("---\ntitle: \"Demo\"\ncreator: Tester\nduration: \"1:23\"\n"
              "hero_frames: []\n---\n\n## TL;DR\n- a **bold** point\n- a [link](https://x)\n\n"
              "## Transcript\n```\n[0:01] hi\n```\n")
    import tempfile
    d = Path(tempfile.mkdtemp())
    (d / "report.md").write_text(sample)
    out = build_html(d / "report.md")
    assert "<h1>Demo</h1>" in out
    assert "<strong>bold</strong>" in out
    assert "<details>" in out and "All frames" not in out
    print("demo OK: frontmatter, bold, link, transcript-collapse all render")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    if not args.report:
        ap.error("report.md required (or --demo)")
    rp = Path(args.report)
    out = Path(args.out) if args.out else rp.parent / "review.html"
    out.write_text(build_html(rp), encoding="utf-8")
    print(out)
    if args.open:
        import platform, subprocess
        opener = os.environ.get("WATCH_VAULT_OPEN_CMD") or (
            "open" if platform.system() == "Darwin"
            else "explorer.exe" if "microsoft" in platform.uname().release.lower()
            else "xdg-open")
        subprocess.run([opener, str(out)], check=False)


if __name__ == "__main__":
    main()
