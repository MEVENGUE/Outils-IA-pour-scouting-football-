import type { StoredDocument } from '../types/player'

const WATCHLIST_KEY = 'xscout-watchlist'
const DOCS_KEY = 'xscout-documents'

export function getWatchlistIds(): number[] {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as number[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveWatchlistIds(ids: number[]) {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(ids))
}

export function toggleWatchlistId(id: number): number[] {
  const current = getWatchlistIds()
  const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id]
  saveWatchlistIds(next)
  return next
}

export function getStoredDocuments(): StoredDocument[] {
  try {
    const raw = localStorage.getItem(DOCS_KEY)
    if (!raw) return []
    return JSON.parse(raw) as StoredDocument[]
  } catch {
    return []
  }
}

export function saveStoredDocuments(docs: StoredDocument[]) {
  localStorage.setItem(DOCS_KEY, JSON.stringify(docs))
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export function countryCodeFromName(country?: string): string | null {
  if (!country) return null
  const map: Record<string, string> = {
    France: 'fr',
    Spain: 'es',
    England: 'gb',
    Germany: 'de',
    Italy: 'it',
    Brazil: 'br',
    Argentina: 'ar',
    Portugal: 'pt',
    Netherlands: 'nl',
    Belgium: 'be',
    Norway: 'no',
    Croatia: 'hr',
    Morocco: 'ma',
    Senegal: 'sn',
    'United Kingdom': 'gb',
    'United States': 'us',
  }
  return map[country] ?? null
}

export async function extractTextFromFile(file: File): Promise<string> {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (['txt', 'csv', 'md', 'json'].includes(ext)) {
    return file.text()
  }
  if (ext === 'pdf') {
    const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs')
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/legacy/build/pdf.worker.min.mjs',
      import.meta.url,
    ).toString()
    const buffer = await file.arrayBuffer()
    const pdf = await pdfjs.getDocument({ data: buffer }).promise
    const pages: string[] = []
    for (let i = 1; i <= pdf.numPages; i += 1) {
      const page = await pdf.getPage(i)
      const content = await page.getTextContent()
      pages.push(content.items.map((item) => ('str' in item ? item.str : '')).join(' '))
    }
    return pages.join('\n')
  }
  throw new Error(`Format .${ext} non supporté pour l'extraction locale. Utilisez TXT, CSV, MD ou PDF.`)
}
