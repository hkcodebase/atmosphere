import { useState, useEffect, useCallback } from 'react'
import { getStats, getDocuments, deleteDocument, uploadFile, scanDocs, searchDocs, queryRAG } from './api'
import './App.css'

const TABS = ['Ask', 'Search', 'Documents', 'Ingest']

export default function App() {
  const [tab, setTab] = useState('Ask')
  const [stats, setStats] = useState(null)
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))

  const refreshStats = useCallback(async () => {
    try { setStats(await getStats()) } catch {}
  }, [])

  useEffect(() => { refreshStats() }, [])

  function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark')
    localStorage.setItem('hk-theme', isDark ? 'dark' : 'light')
    setDark(isDark)
  }

  return (
    <>
      <nav className="nav">
        <span className="nav-logo">RAG</span>
        <div className="nav-right">
          {TABS.map(t => (
            <button key={t} className={`nav-link ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
          <button className="theme-btn" onClick={toggleTheme} title="Toggle light / dark">◐</button>
        </div>
      </nav>

      <main>
        {stats && (
          <div className="stats-row">
            <div className="stat-item">
              <span className="stat-n">{stats.documents}</span>
              <span className="stat-label">Documents</span>
            </div>
            <div className="stat-item">
              <span className="stat-n">{stats.chunks}</span>
              <span className="stat-label">Chunks</span>
            </div>
          </div>
        )}

        {tab === 'Ask'       && <AskTab />}
        {tab === 'Search'    && <SearchTab />}
        {tab === 'Documents' && <DocumentsTab onActivity={refreshStats} />}
        {tab === 'Ingest'    && <IngestTab onActivity={refreshStats} />}
      </main>

      <footer>
        <span>RAG Document Search</span>
        <span>Gemma · Neo4j · Docker Model Runner</span>
      </footer>
    </>
  )
}

// ── Ask ───────────────────────────────────────────────────────────────────────

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
    try { setResult(await queryRAG(question, topK)) }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="panel">
      <p className="label">Ask</p>
      <p className="panel-subtitle">Gemma answers using your documents as context.</p>

      <form onSubmit={handleAsk}>
        <div className="field">
          <textarea
            rows={3}
            placeholder="What would you like to know about your documents?"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(e) } }}
          />
        </div>
        <div className="field-row">
          <label className="field-label">
            Top-K sources
            <input type="number" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} />
          </label>
          <button className="btn btn-primary" disabled={loading || !question.trim()}>
            {loading ? 'Thinking…' : 'Ask Gemma →'}
          </button>
        </div>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {result && (
        <div className="answer-block">
          <p className="answer-kicker">Answer</p>
          <p className="answer-text">{result.answer}</p>

          {result.sources?.length > 0 && (
            <>
              <p className="sources-kicker">Sources ({result.sources.length})</p>
              {result.sources.map((s, i) => <SourceRow key={i} source={s} index={i} />)}
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ── Search ────────────────────────────────────────────────────────────────────

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
    try { setResults((await searchDocs(query, topK)).results) }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="panel">
      <p className="label">Search</p>
      <p className="panel-subtitle">Semantic similarity search — finds relevant chunks without LLM generation.</p>

      <form onSubmit={handleSearch}>
        <div className="field">
          <input placeholder="Search your documents…" value={query} onChange={e => setQuery(e.target.value)} />
        </div>
        <div className="field-row">
          <label className="field-label">
            Results
            <input type="number" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} />
          </label>
          <button className="btn btn-primary" disabled={loading || !query.trim()}>
            {loading ? 'Searching…' : 'Search →'}
          </button>
        </div>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {results && (
        <div style={{ marginTop: 24 }}>
          <p className="sources-kicker">{results.length} result{results.length !== 1 ? 's' : ''}</p>
          {results.map((s, i) => <SourceRow key={i} source={s} index={i} showScore />)}
          {results.length === 0 && <p className="empty">No results found.</p>}
        </div>
      )}
    </div>
  )
}

// ── Documents ─────────────────────────────────────────────────────────────────

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
      <p className="label">Documents</p>
      <p className="panel-subtitle">All documents currently indexed in Neo4j.</p>

      {loading && <p className="empty">Loading…</p>}
      {!loading && docs.length === 0 && <p className="empty">No documents indexed yet. Use the Ingest tab to add some.</p>}

      {docs.map((d, i) => (
        <div key={d.id} className="doc-row">
          <span className="doc-num">{String(i + 1).padStart(2, '0')}</span>
          <div className="doc-body">
            <p className="doc-name">{d.name}</p>
            <p className="doc-path">{d.path}</p>
          </div>
          <div className="doc-right">
            <span className="doc-chunks">{d.chunks} chunks</span>
            <button
              className="btn btn-danger"
              onClick={() => handleDelete(d.id)}
              disabled={deleting === d.id}
            >
              {deleting === d.id ? '…' : 'Delete'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Ingest ────────────────────────────────────────────────────────────────────

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
      setUploadResult({ ok: true, ...r }); onActivity()
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
      <p className="label">Ingest</p>
      <p className="panel-subtitle">Supported formats: PDF · DOCX · TXT · MD · XLSX · XLS</p>

      <div className="ingest-section">
        <h3>Upload a file</h3>
        <div
          className={`dropzone${dragOver ? ' drag-over' : ''}${uploading ? ' uploading' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => !uploading && document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            style={{ display: 'none' }}
            accept=".pdf,.docx,.txt,.md,.xlsx,.xls"
            onChange={e => e.target.files[0] && handleUpload(e.target.files[0])}
          />
          {uploading ? 'Uploading and ingesting…' : 'Drop a file here or click to browse'}
        </div>
        {uploadResult && (
          <div className={`alert ${uploadResult.ok ? 'alert-success' : 'alert-error'}`}>
            {uploadResult.ok
              ? `${uploadResult.status === 'skipped' ? 'Skipped (unchanged)' : `Ingested — ${uploadResult.chunks} chunks`} · ${uploadResult.path}`
              : uploadResult.error}
          </div>
        )}
      </div>

      <div className="ingest-section">
        <h3>Scan mounted documents folder</h3>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
          Scans the <code style={{ fontSize: 12 }}>/docs</code> folder mounted in the API container (set via <code style={{ fontSize: 12 }}>DOCS_FOLDER</code> in <code style={{ fontSize: 12 }}>.env</code>).
        </p>
        <button className="btn btn-primary" onClick={handleScan} disabled={scanning}>
          {scanning ? 'Scanning…' : 'Scan & Ingest All →'}
        </button>

        {scanLog.length > 0 && (
          <div className="scan-log">
            {scanLog.map((entry, i) => (
              <div key={i} className="log-line">
                <span className="log-status">{entry.status}</span>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {entry.path}
                </span>
                {entry.chunks != null && <span style={{ whiteSpace: 'nowrap' }}>{entry.chunks} chunks</span>}
                {entry.error && <span className="log-error-text">{entry.error}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Source row (shared) ───────────────────────────────────────────────────────

function SourceRow({ source, index, showScore }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="source-row" onClick={() => setOpen(o => !o)}>
      <span className="source-num">{String(index + 1).padStart(2, '0')}</span>
      <div className="source-body">
        <p className="source-doc">{source.document || source.source}</p>
        <p className="source-meta">
          {source.source}
          {source.page > 0 && ` · p.${source.page}`}
        </p>
        <p className={`source-excerpt ${open ? 'open' : ''}`}>{source.text}</p>
      </div>
      <div className="source-right">
        {showScore && <span className="source-score">{(source.score * 100).toFixed(1)}%</span>}
        <span className="source-arrow">{open ? '↑' : '↗'}</span>
      </div>
    </div>
  )
}
