export const meta = {
  name: 'watch-vault-full',
  description: 'Batch YouTube ingest: download, analyze, research, ingest, generate HTML reviews',
  phases: [
    { title: 'Download & Frame Extract', detail: 'Parallel video downloads via watch.py' },
    { title: 'Analyze', detail: 'Parallel Sonnet analyst sub-agents per video' },
    { title: 'Research', detail: 'Parallel Sonnet researcher sub-agents for Resources & Reality-check' },
    { title: 'Ingest', detail: 'Confirm categories, move files, create topic notes' },
    { title: 'Publish', detail: 'Generate HTML reviews and open' },
  ],
}

import { execSync } from 'child_process'

const VAULT = process.env.WATCH_VAULT_DIR || '/Users/chrismckenna/Documents/Obsidian Vault'
const COOKIES = process.env.WATCH_COOKIES_FROM_BROWSER || 'safari'
const SKILL_PATH = '/Users/chrismckenna/.claude/skills/watch-vault'

const slugify = (s) => s.toLowerCase().replace(/\W+/g, '-').slice(0, 50)
const today = new Date().toISOString().split('T')[0]

// ============================================================================
// PHASE 1: Download all videos in parallel
// ============================================================================

phase('Download & Frame Extract')

const urls = Array.isArray(args) ? args : [args].filter(Boolean)
if (!urls.length) throw new Error('No URLs provided to watch-vault')

log(`Batch watch-vault: ${urls.length} video(s)`)

// Execute watch.py for each URL in parallel via shell, extract workdir from output
const downloadResults = await parallel(
  urls.map((url, idx) => async () => {
    const sanitized = url.replace(/"/g, '\\"')
    const cmd = `WATCH_COOKIES_FROM_BROWSER=${COOKIES} python3 ${SKILL_PATH}/../watch/scripts/watch.py "${sanitized}" --intent "general summary" 2>&1`

    try {
      const output = execSync(cmd, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 })
      const workdirMatch = output.match(/\[watch\] working dir: (.+)/)
      const workdir = workdirMatch ? workdirMatch[1].trim() : null

      if (!workdir) throw new Error('Could not extract workdir from watch.py output')

      return { url, workdir, status: 'downloaded' }
    } catch (err) {
      log(`❌ Download failed for video ${idx + 1}: ${err.message}`)
      return { url, workdir: null, status: 'failed', error: err.message }
    }
  })
)

const videos = downloadResults.filter(r => r.workdir).map((r, idx) => ({
  ...r,
  id: idx,
  slug: `video-${idx + 1}`,
}))

if (videos.length === 0) throw new Error('No videos downloaded successfully')
log(`✓ Downloaded ${videos.length}/${urls.length} videos`)

// ============================================================================
// PHASE 2: Analyze each video (parallel)
// ============================================================================

phase('Analyze')

const analyzed = await parallel(
  videos.map(v => async () => {
    const result = await agent(
      `Analyze video: extract title, creator, category, summary, confidence level.

      WORKDIR: ${v.workdir}

      1. Run: python3 ${SKILL_PATH}/scripts/compact_transcript.py ${v.workdir}/report.md --out ${v.workdir}/paras.txt
      2. Read paras.txt in full
      3. Read 15 hero+spread frames (cap 15 total)
      4. Fill all "<!-- pending Claude fill: ... -->" markers in report.md via Edit
      5. Verify: grep -c 'pending Claude fill' should == 0
      6. Return ONLY (plain text, no markdown):
         title: [title]
         duration: [duration]
         creator: [creator]
         suggested_category: [category + reason]
         summary: [4–6 sentences]
         flags: ⚠️ [if any]
         confidence: high|low
         dense: yes|no

      Frames: ${v.workdir}/frames/`,
      {
        label: `analyst:${v.id + 1}`,
        phase: 'Analyze',
        model: 'sonnet',
      }
    )

    // Parse the text response into structured fields
    const lines = result.split('\n').map(l => l.trim()).filter(Boolean)
    const parsed = {}
    for (const line of lines) {
      const [key, ...val] = line.split(':')
      if (key && val.length) parsed[key.trim()] = val.join(':').trim()
    }

    return { ...v, analysis: parsed }
  })
)

log(`✓ Analyzed ${analyzed.length} videos`)

// ============================================================================
// PHASE 3: Research each video (parallel)
// ============================================================================

phase('Research')

const researched = await parallel(
  analyzed.map(v => async () => {
    const result = await agent(
      `Append Resources & Reality-check sections to video report.

REPORT: ${v.workdir}/report.md

TASK:
1. Read report.md
2. For EVERY software/tool/site mentioned, web-search official source
3. APPEND before "## Transcript":

## Resources & how to get them
- For each tool: URL + repo + install (CLI/GUI) + docs link

4. APPEND Reality check section:

## Reality check (1 = true · 10 = hype)
- **Overall video: [N/10]** — one-line why
- ~5–8 bullets: \`- **[N/10]** *"quote"* — verdict — evidence ([source](url))\`
- Format scores as \`[N/10]\`

5. Return ONLY (plain text): overall_hype_score: [N/10]`,
      {
        label: `researcher:${v.id + 1}`,
        phase: 'Research',
        model: 'sonnet',
      }
    )

    const scoreMatch = result.match(/overall_hype_score:\s*(\d+)\/10/)
    const hypeScore = scoreMatch ? parseInt(scoreMatch[1]) : 5

    return { ...v, hypeScore }
  })
)

log(`✓ Researched ${researched.length} videos`)

// ============================================================================
// PHASE 4: Ingest into vault
// ============================================================================

phase('Ingest')

const ingested = []
for (const v of researched) {
  const cat = v.analysis.suggested_category?.split(' ')[0] || 'AI'
  const catFolder = cat === 'Stock' ? 'Stock Trading' : 'AI'

  const slug = `${slugify(v.analysis.title || 'video')}-${today}`
  const watchPath = `${VAULT}/${catFolder}/watched/${slug}`

  try {
    // Create dirs, move report + frames
    execSync(`mkdir -p "${watchPath}"`)
    execSync(`cp "${v.workdir}/report.md" "${watchPath}/"`)
    execSync(`cp "${v.workdir}"/frames/frame_000{1,3,5,8,9}.jpg "${watchPath}/" 2>/dev/null || true`)

    // Append to log.md
    const logFile = `${VAULT}/${catFolder}/log.md`
    const logLine = `- ${today} — [[${slug}]] — *${v.analysis.title}* (${v.analysis.creator}): ${v.analysis.summary?.slice(0, 80)}… → ${catFolder}/watched/${slug}/report.md`
    execSync(`echo "${logLine}" >> "${logFile}"`)

    ingested.push({ ...v, slug, catFolder, watchPath })
  } catch (err) {
    log(`⚠️ Ingest issue for video ${v.id + 1}: ${err.message}`)
  }
}

log(`✓ Ingested ${ingested.length} videos into vault`)

// ============================================================================
// PHASE 5: Generate HTML & Open
// ============================================================================

phase('Publish')

const htmlFiles = []
await parallel(
  ingested.map(v => async () => {
    try {
      const reportPath = `${v.watchPath}/report.md`
      const cmd = `python3 ${SKILL_PATH}/scripts/report_to_html.py "${reportPath}"`
      execSync(cmd)
      htmlFiles.push(`${v.watchPath}/review.html`)
    } catch (err) {
      log(`⚠️ HTML generation failed for ${v.slug}: ${err.message}`)
    }
  })
)

log(`✓ Generated ${htmlFiles.length} HTML reviews`)
log(`📂 Check vault: ${VAULT}`)

// Return summary
return {
  message: `✓ watch-vault batch complete: ${ingested.length} videos ingested`,
  videos: ingested.map(v => ({
    title: v.analysis.title,
    category: v.catFolder,
    hypeScore: v.hypeScore,
    path: v.watchPath,
    reviewHtml: `${v.watchPath}/review.html`,
  })),
}
