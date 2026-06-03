import { useState, useEffect, useCallback } from 'react'
import { getStats, getDocuments, deleteDocument, uploadFile, scanDocs, searchDocs, queryRAG } from './api'
import './App.css'

const TABS = ['Ask', 'Search', 'Documents', 'Ingest']

export default function App() {
  const [tab, setTab] = useState('Ask')
  const [stats, setStats] = useState(null)

  const refreshStats = useCallback(async () => {
    try { setStats(await getStats()) } catch {}
  }, [])

  useEffect(() => { refreshStats() }, [])

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-icon">◈</span>
          <span>RAG Search</span>
        </div>
        <nav>
          {TABS.map(t => (
            <button
              key={t}
              className={`nav-btn ${tab === t ? 'active' : ''}`}
              onClick={() => setTab(t)}
            >
              {tabIcon(t)} {t}
            </button>
          ))}
        </nav>
        {stats && (
          <div className="stats-card">
            <div className="stat"><span className="stat-n">{stats.documents}</span><span>Documents</span></div>
            <div className="stat"><span className="stat-n">{stats.chunks}</span><span>Chunks</span></div>
          </div>
        )}
      </aside>

      <main className="content">
        {tab === 'Ask'       && <AskTab onActivity={refreshStats} />}
        {tab === 'Search'    && <SearchTab />}
        {tab === 'Documents' && <DocumentsTab onActivity={refreshStats} />}
        {tab === 'Ingest'    && <IngestTab onActivity={refreshStats} />}
      </main>
    </div>
  )
}

function tabIcon(t) {
  return { Ask: '💬', Search: '🔍', Documents: '📄', Ingest: '📥' }[t]
}

// ── Ask Tab ──────────────────────────────────────────────────────────────────

function AskTab() {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAsk(e) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      setResult(await queryRAG(question, topK))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Ask a Question</h2>
      <p className="subtitle">Gemma answers using your documents as context.</p>
      <form onSubmit={handleAsk} className="ask-form">
        <textarea
          rows={3}
          placeholder="What would you like to know about your documents?"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(e) } }}
        />
        <div className="form-row">
          <label className="inline-label">
            Top-K sources
            <input type="number" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} style={{ width: 60, marginLeft: 8 }} />
          </label>
          <button className="btn-primary" disabled={loading || !question.trim()}>
            {loading ? 'Thinking…' : 'Ask Gemma'}
          </button>
        </div>
      </form>

      {error && <div className="alert-error">{error}</div>}

      {result && (
        <div className="result-block">
          <div className="answer-box">
            <div className="answer-label">Answer</div>
            <p className="answer-text">{result.answer}</p>
          </div>
          {result.sources?.length > 0 && (
            <div className="sources">
              <div className="sources-label">Sources used ({result.sources.length})</div>
              {result.sources.map((s, i) => <SourceCard key={i} source={s} index={i} />)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Search Tab ────────────────────────────────────────────────────────────────

function SearchTab() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true); setError(null)
    try {
      const data = await searchDocs(query, topK)
      setResults(data.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Semantic Search</h2>
      <p className="subtitle">Find relevant chunks across your documents by meaning.</p>
      <form onSubmit={handleSearch} className="ask-form">
        <input placeholder="Search your documents…" value={query} onChange={e => setQuery(e.target.value)} />
        <div className="form-row">
          <label className="inline-label">
            Results
            <input type="number" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} style={{ width: 60, marginLeft: 8 }} />
          </label>
          <button className="btn-primary" disabled={loading || !query.trim()}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </form>

      {error && <div className="alert-error">{error}</div>}

      {results && (
        <div className="result-block">
          <div className="sources-label">{results.length} result{results.length !== 1 ? 's' : ''}</div>
          {results.map((s, i) => <SourceCard key={i} source={s} index={i} showScore />)}
        </div>
      )}
    </div>
  )
}

// ── Documents Tab ─────────────────────────────────────────────────────────────

function DocumentsTab({ onActivity }) {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  async function load() {
    setLoading(true)
    try { setDocs((await getDocuments()).documents) } catch {}
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  async function handleDelete(id) {
    setDeleting(id)
    try { await deleteDocument(id); await load(); onActivity() } catch {}
    setDeleting(null)
  }

  return (
    <div className="panel">
      <h2>Indexed Documents</h2>
      <p className="subtitle">All documents currently stored in Neo4j.</p>
      {loading && <div className="muted">Loading…</div>}
      {!loading && docs.length === 0 && <div className="empty-state">No documents indexed yet. Use the Ingest tab to add some.</div>}
      <div className="doc-list">
        {docs.map(d => (
          <div key={d.id} className="doc-card">
            <div className="doc-info">
              <span className="doc-name">{d.name}</span>
              <span className="doc-path muted">{d.path}</span>
            </div>
            <div className="doc-meta">
              <span className="tag tag-blue">{d.chunks} chunks</span>
              <button
                className="btn-danger"
                onClick={() => handleDelete(d.id)}
                disabled={deleting === d.id}
              >
                {deleting === d.id ? '…' : 'Delete'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Ingest Tab ────────────────────────────────────────────────────────────────

function IngestTab({ onActivity }) {
  const [scanLog, setScanLog] = useState([])
  const [scanning, setScanning] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  async function handleScan() {
    setScanning(true); setScanLog([])
    try {
      await scanDocs(line => setScanLog(prev => [...prev, line]))
      onActivity()
    } catch (e) {
      setScanLog(prev => [...prev, { status: 'error', error: e.message }])
    }
    setScanning(false)
  }

  async function handleUpload(file) {
    setUploading(true); setUploadResult(null)
    try {
      const r = await uploadFile(file)
      setUploadResult({ ok: true, ...r })
      onActivity()
    } catch (e) {
      setUploadResult({ ok: false, error: e.message })
    }
    setUploading(false)
  }

  function onDrop(e) {
    e.preventDefault(); setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="panel">
      <h2>Ingest Documents</h2>
      <p className="subtitle">Supported: PDF, DOCX, TXT, MD, XLSX, XLS</p>

      <section className="ingest-section">
        <h3>Upload a file</h3>
        <div
          className={`dropzone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            style={{ display: 'none' }}
            accept=".pdf,.docx,.txt,.md,.xlsx,.xls"
            onChange={e => e.target.files[0] && handleUpload(e.target.files[0])}
          />
          {uploading ? <span>Uploading and ingesting…</span> : <span>Drop a file here or <u>click to browse</u></span>}
        </div>
        {uploadResult && (
          <div className={uploadResult.ok ? 'alert-success' : 'alert-error'}>
            {uploadResult.ok
              ? `✓ ${uploadResult.status === 'skipped' ? 'Skipped (unchanged)' : `Ingested ${uploadResult.chunks} chunks`} — ${uploadResult.path}`
              : `✗ ${uploadResult.error}`}
          </div>
        )}
      </section>

      <section className="ingest-section">
        <h3>Scan mounted documents folder</h3>
        <p className="muted" style={{ marginBottom: '0.8rem' }}>
          Scans the <code>/docs</code> folder mounted in the API container (set via <code>DOCS_FOLDER</code> in <code>.env</code>).
        </p>
        <button className="btn-primary" onClick={handleScan} disabled={scanning}>
          {scanning ? 'Scanning…' : 'Scan & Ingest All'}
        </button>
        {scanLog.length > 0 && (
          <div className="scan-log">
            {scanLog.map((entry, i) => (
              <div key={i} className={`log-line log-${entry.status}`}>
                <span className={`tag tag-${statusColor(entry.status)}`}>{entry.status}</span>
                {' '}{entry.path}
                {entry.chunks != null && <span className="muted"> · {entry.chunks} chunks</span>}
                {entry.error && <span className="log-error"> · {entry.error}</span>}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

// ── Shared components ─────────────────────────────────────────────────────────

function SourceCard({ source, index, showScore }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="source-card">
      <div className="source-header" onClick={() => setExpanded(e => !e)}>
        <span className="source-idx">#{index + 1}</span>
        <span className="source-doc">{source.document || source.source}</span>
        {source.page > 0 && <span className="muted">p.{source.page}</span>}
        {showScore && <span className="tag tag-blue">{(source.score * 100).toFixed(1)}%</span>}
        <span className="chevron">{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && <div className="source-text">{source.text}</div>}
    </div>
  )
}

function statusColor(s) {
  return { ingested: 'green', skipped: 'yellow', error: 'red' }[s] || 'blue'
}
