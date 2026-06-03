const BASE = '/api'

export async function getStats() {
  const r = await fetch(`${BASE}/stats`)
  if (!r.ok) throw new Error('Failed to fetch stats')
  return r.json()
}

export async function getDocuments() {
  const r = await fetch(`${BASE}/documents`)
  if (!r.ok) throw new Error('Failed to fetch documents')
  return r.json()
}

export async function deleteDocument(id) {
  const r = await fetch(`${BASE}/documents/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Failed to delete document')
  return r.json()
}

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const r = await fetch(`${BASE}/ingest/upload`, { method: 'POST', body: form })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || 'Upload failed')
  }
  return r.json()
}

export async function scanDocs(onLine) {
  const r = await fetch(`${BASE}/ingest/scan`, { method: 'POST' })
  if (!r.ok) throw new Error('Scan failed')
  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const lines = decoder.decode(value).split('\n').filter(Boolean)
    for (const line of lines) {
      try { onLine(JSON.parse(line)) } catch {}
    }
  }
}

export async function searchDocs(query, topK = 5) {
  const r = await fetch(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  })
  if (!r.ok) throw new Error('Search failed')
  return r.json()
}

export async function queryRAG(question, topK = 5) {
  const r = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  })
  if (!r.ok) throw new Error('Query failed')
  return r.json()
}
