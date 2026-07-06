# Obsidian Vault — Ingest rules (watch-vault)

This file tells watch-vault (and any agent) how to file a finished `report.md` into this
vault. **Customize the Categories below** to match how you think — the Ingest op stays the same.

## Categories

Route every ingest into exactly one category folder by topic. Edit this table freely;
add/remove rows. Keep the "Default / tie-breaker" line so routing is never ambiguous.

| Category      | Use for                                                                 |
|---------------|-------------------------------------------------------------------------|
| `AI/`         | AI, LLMs, agents, coding tools, ML, developer tech.                     |
| `Finance/`    | Personal finance, investing, business/money, entrepreneurship.          |
| `Health/`     | Fitness, nutrition, sleep, medical, mental health.                      |
| `Learning/`   | Skills, tutorials, how-to, education on any other topic.                |

**Default / tie-breaker:** if a video spans two categories, file it under the one matching
its *primary actionable mechanic* (e.g. a "use ChatGPT to pick a business" video is Finance
if the payoff is the business, AI if the payoff is the prompt technique). State the pick and
why in chat; the user can redirect it.

## Ingest op

Let `CAT` = the category folder chosen above, `SLUG` = report title slugified + `-YYYY-MM-DD`.

1. **Stage the raw report** at `CAT/watched/<SLUG>/report.md` (create dirs as needed). Copy the
   hero frames + `review.html` alongside it. If the report was pre-staged under
   `raw/watched/<SLUG>/`, move it to `CAT/watched/<SLUG>/` instead of leaving a duplicate.
2. **Append one line to `CAT/log.md`** (create if missing), matching the existing format:
   `- YYYY-MM-DD — [[<SLUG>]] — *<Title>* (<Creator>): <one-line gist>. ⚠️ <flags> · reality-check <N>/10. → CAT/watched/<SLUG>/report.md`
3. **Write a polished topic note** at `CAT/<Title>.md` (strip `|`/`:` from the filename) with
   this frontmatter, then a readable summary distilled from the report (not the raw transcript):
   ```yaml
   ---
   title: "<Title>"
   category: <CAT without trailing slash>
   source: <url>
   creator: <channel/author>
   duration: "<MM:SS>"
   watched: <YYYY-MM-DD>
   tags: [<kebab-case topic tags>]
   hype_score: "<N>/10 — <one-line why>"
   disclaimer: "<promotional / not-advice notes, if any>"
   related: "<[[wikilinks]] to sibling notes in the same category, if any>"
   ---
   ```
   Body: a `>` callout TL;DR, a `> 🖥️ [Review page](watched/<SLUG>/review.html)` link, a
   `> ⚖️ Reality check` callout (overall `[N/10]` + worst offenders), a `> 📥 Get it` line
   (official link + install one-liner for any software), then the key takeaways as `##`
   sections. Link siblings with `[[wikilinks]]`. Flag promotional/unverified claims with ⚠️.
4. **Report back** in chat: the topic-note path, the `CAT/watched/<SLUG>/` report + review.html
   paths, the `CAT/log.md` line, and the overall reality-check score.

## Disclaimer rule

Creator content is often promotional. Preserve any "not advice" note from the creator, mark
hyped claims with ⚠️, and never present a creator's numbers as verified. The Reality-check
section (1 = true … 10 = hype) is where claims get scored against independent sources.
