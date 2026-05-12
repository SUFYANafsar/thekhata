/**
 * One-off blog MDX refactor (plan: author rename, title sync, article id, dates policy A).
 * Run: node scripts/refactor-blog-mdx.mjs
 *
 * Edit constants below if you need different names or modified timestamp.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BLOG_DIR = path.join(__dirname, '..', 'src', 'content', 'blog')

/** Policy A: keep published; set modified to this ISO string */
const MODIFIED_ISO = '2026-05-12T12:00:00+00:00'

/** Display names (two authors, same /author/... URLs) */
const AUTHOR_BY_SLUG_SEGMENT = {
  '2samaaprmzesd': { display: 'Usama M.', postsBy: 'Posts by Usama M.' },
  '2hitooraaprmzesd': { display: 'Z. Riaz', postsBy: 'Posts by Z. Riaz' },
}

function parseFrontmatter(text) {
  if (!text.startsWith('---\n')) throw new Error('Expected --- frontmatter')
  const end = text.indexOf('\n---\n', 4)
  if (end === -1) throw new Error('Missing closing ---')
  const raw = text.slice(4, end)
  const rest = text.slice(end + 5)
  const map = {}
  for (const line of raw.split('\n')) {
    const m = line.match(/^([a-zA-Z0-9_]+):\s*(.*)$/)
    if (m) map[m[1]] = m[2].trim()
  }
  return { raw, map, rest }
}

function yamlQuoteString(s) {
  if (/[\n"]/.test(s)) {
    return JSON.stringify(s)
  }
  if (/^[a-zA-Z0-9\-_.:/\s]+$/.test(s) && !s.includes("'")) {
    return `'${s.replace(/'/g, "''")}'`
  }
  return JSON.stringify(s)
}

function setYamlField(raw, key, newValue) {
  const lines = raw.split('\n')
  const q = yamlQuoteString(newValue)
  let found = false
  const out = lines.map((line) => {
    if (new RegExp(`^${key}:`).test(line)) {
      found = true
      return `${key}: ${q}`
    }
    return line
  })
  if (!found) out.push(`${key}: ${q}`)
  return out.join('\n')
}

function decodeHtmlEntities(s) {
  return s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&#8217;/g, "'")
    .replace(/&#8220;/g, '"')
    .replace(/&#8221;/g, '"')
    .replace(/&nbsp;/g, ' ')
}

function stripTags(html) {
  return decodeHtmlEntities(html.replace(/<[^>]+>/g, '')).trim()
}

function formatPublishedSpan(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function transformHtml(html, slug) {
  let out = html

  const h1m = out.match(/<h1 class="entry-title">([\s\S]*?)<\/h1>/)
  const h1Plain = h1m ? stripTags(h1m[1]) : null

  out = out.replace(
    /<article id="post-(\d+)"/g,
    `<article id="blog-${slug}" data-wp-post-id="$1"`
  )

  for (const [segment, a] of Object.entries(AUTHOR_BY_SLUG_SEGMENT)) {
    const hrefPath = `/author/${segment}/`
    const re = new RegExp(
      `(<a href="${hrefPath.replace(/\//g, '\\/')}"[^>]*title=")([^"]+)("[^>]*>)([^<]*)(</a>)`,
      'g'
    )
    out = out.replace(re, (_, p1, _oldTitle, p3, _oldName, p5) => {
      return `${p1}${a.postsBy}${p3}${a.display}${p5}`
    })
  }

  return { html: out, h1Plain }
}

function processFile(filePath) {
  const text = fs.readFileSync(filePath, 'utf8')
  const { raw, map, rest } = parseFrontmatter(text)
  const slug = map.slug?.replace(/^["']|["']$/g, '') || ''
  if (!slug) throw new Error(`No slug in ${filePath}`)

  const tag = 'set:html={`'
  const i = rest.indexOf(tag)
  if (i === -1) throw new Error(`No set:html in ${filePath}`)
  const j = rest.lastIndexOf('`} />')
  if (j === -1 || j <= i) throw new Error(`No closing backtick in ${filePath}`)

  const prefix = rest.slice(0, i + tag.length)
  let html = rest.slice(i + tag.length, j)
  const suffix = rest.slice(j)

  const { html: html2, h1Plain } = transformHtml(html, slug)
  html = html2

  const publishedIso = map.published?.replace(/^["']|["']$/g, '') || ''
  const span = formatPublishedSpan(publishedIso)
  if (span) {
    html = html.replace(
      /<span class="published">[^<]*<\/span>/,
      `<span class="published">${span}</span>`
    )
  }

  let newFm = setYamlField(raw, 'modified', MODIFIED_ISO)
  if (h1Plain) {
    newFm = setYamlField(newFm, 'title', h1Plain)
  }

  const out = `---\n${newFm}\n---\n${prefix}${html}${suffix}`
  fs.writeFileSync(filePath, out, 'utf8')
  return { slug, h1Plain }
}

const files = fs.readdirSync(BLOG_DIR).filter((f) => f.endsWith('.mdx'))
for (const f of files) {
  processFile(path.join(BLOG_DIR, f))
  console.log('OK', f)
}
console.log('Done', files.length, 'files')
