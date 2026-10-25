import React, { useEffect, useState, useCallback, useRef } from 'react'
import api from '../api/client'
import type { Export, ExportListResponse, ExportRequest, JobListResponse } from '../types'
import { format } from 'date-fns'
import { Download, Trash2, Plus, FileSpreadsheet, AlertTriangle, X, RotateCcw } from 'lucide-react'

// ── Generate Export Modal ──────────────────────────────────
function GenerateModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState<ExportRequest>({ min_score: undefined, limit: 1000 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [matchCount, setMatchCount] = useState<number | null>(null)
  const [checkingCount, setCheckingCount] = useState(false)
  const debounceTimer = useRef<any>(null)

  const set = (k: keyof ExportRequest, v: any) => {
    setForm(f => ({ ...f, [k]: v || undefined }))
  }

  // Live count preview
  useEffect(() => {
    clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(async () => {
      setCheckingCount(true)
      try {
        const params = new URLSearchParams()
        params.append('page', '1')
        params.append('page_size', '1')
        if (form.min_score !== undefined) params.append('min_score', String(form.min_score))
        if (form.company) params.append('company', form.company)
        if (form.date_from) params.append('date_from', form.date_from)
        if (form.date_to) params.append('date_to', form.date_to)

        const { data: res } = await api.get<JobListResponse>(`/jobs?${params.toString()}`)
        setMatchCount(res.total)
      } catch {
        setMatchCount(null)
      } finally {
        setCheckingCount(false)
      }
    }, 250)

    return () => clearTimeout(debounceTimer.current)
  }, [form.min_score, form.company, form.date_from, form.date_to])

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.post('/exports', form)
      onDone()
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to generate export')
    } finally {
      setLoading(false)
    }
  }

  const clearDates = () => {
    setForm(f => ({ ...f, date_from: undefined, date_to: undefined }))
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">Generate New Export</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 14 }}><AlertTriangle size={15} />{error}</div>}

        <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="grid-2">
            <div className="form-group">
              <label className="label">Min Match Score</label>
              <input type="number" min={0} max={100} className="input" placeholder="0 = all" value={form.min_score ?? ''} onChange={e => set('min_score', e.target.value ? parseInt(e.target.value) : undefined)} />
            </div>
            <div className="form-group">
              <label className="label">Max Rows</label>
              <input type="number" min={1} max={5000} className="input" value={form.limit ?? 1000} onChange={e => set('limit', parseInt(e.target.value) || 1000)} />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="label">Date From</label>
                {form.date_from && (
                  <button type="button" onClick={() => set('date_from', undefined)} style={{ background: 'none', border: 'none', color: 'var(--accent)', fontSize: 11, cursor: 'pointer', padding: 0 }}>
                    Clear
                  </button>
                )}
              </div>
              <input type="date" className="input" value={form.date_from ?? ''} onChange={e => set('date_from', e.target.value)} />
            </div>
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="label">Date To</label>
                {form.date_to && (
                  <button type="button" onClick={() => set('date_to', undefined)} style={{ background: 'none', border: 'none', color: 'var(--accent)', fontSize: 11, cursor: 'pointer', padding: 0 }}>
                    Clear
                  </button>
                )}
              </div>
              <input type="date" className="input" value={form.date_to ?? ''} onChange={e => set('date_to', e.target.value)} />
            </div>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: -6 }}>
            💡 Tip: Leave both date fields empty to export all available leads in the database.
          </div>

          <div className="form-group">
            <label className="label">Filter by Company</label>
            <input className="input" placeholder="Leave blank for all" value={form.company ?? ''} onChange={e => set('company', e.target.value)} />
          </div>

          {/* Lead count preview badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-subtle, rgba(255,255,255,0.04))',
            padding: '10px 14px',
            borderRadius: 6,
            border: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
            fontSize: 12
          }}>
            <span style={{ color: 'var(--text-secondary)' }}>Matching leads ready to export:</span>
            <span style={{ fontWeight: 700, color: matchCount === 0 ? 'var(--red)' : 'var(--green)' }}>
              {checkingCount ? 'Checking…' : matchCount !== null ? `${matchCount.toLocaleString()} leads` : '—'}
            </span>
          </div>

          {matchCount === 0 && (
            <div className="alert alert-warn" style={{ fontSize: 12, padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>No leads match these criteria. Try clearing the date filters or running a scrape.</span>
              {(form.date_from || form.date_to) && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  style={{ height: 'auto', padding: '3px 8px', fontSize: 11 }}
                  onClick={clearDates}
                >
                  <RotateCcw size={11} /> Clear Dates
                </button>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 6 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || matchCount === 0}
              title={matchCount === 0 ? "No matching leads to export" : "Generate Excel spreadsheet"}
            >
              {loading ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <FileSpreadsheet size={14} />}
              Generate Excel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────
export default function ExportsPage() {
  const [data, setData] = useState<ExportListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data: res } = await api.get<ExportListResponse>('/exports')
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this export? This cannot be undone.')) return
    setDeleting(id)
    try {
      await api.delete(`/exports/${id}`)
      load()
    } finally {
      setDeleting(null)
    }
  }

  const handleDownload = async (exp: Export) => {
    setDownloadingId(exp.id)
    try {
      // 1. Fetch via authenticated Axios instance (carries Bearer token in headers)
      const res = await api.get(exp.download_url, { responseType: 'blob' })
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', exp.filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Blob download failed, falling back to direct token query:', err)
      const token = localStorage.getItem('access_token')
      if (token) {
        window.open(`/api${exp.download_url}?token=${encodeURIComponent(token)}`, '_blank')
      } else {
        alert('Download failed. Please log in again.')
      }
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Exports</h1>
            <p className="page-subtitle">Generated Excel spreadsheets from past pipeline runs</p>
          </div>
          <button id="generate-export-btn" className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={15} /> Generate Export
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* Stats summary */}
        {data && data.items.length > 0 && (
          <div className="grid-3" style={{ marginBottom: 20 }}>
            <div className="stat-card accent">
              <div className="stat-label">Total Exports</div>
              <div className="stat-value">{data.total}</div>
            </div>
            <div className="stat-card green">
              <div className="stat-label">Total Rows</div>
              <div className="stat-value">{data.items.reduce((s, e) => s + e.row_count, 0).toLocaleString()}</div>
            </div>
            <div className="stat-card amber">
              <div className="stat-label">Avg Match Score</div>
              <div className="stat-value">
                {(data.items.reduce((s, e) => s + e.avg_match_score, 0) / data.items.length).toFixed(1)}%
              </div>
            </div>
          </div>
        )}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Rows</th>
                <th>Avg Score</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr><td colSpan={5}>
                  <div className="empty-state">
                    <FileSpreadsheet size={40} />
                    <div>No exports yet</div>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>Generate first export</button>
                  </div>
                </td></tr>
              ) : (data?.items ?? []).map(exp => (
                <tr key={exp.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileSpreadsheet size={16} style={{ color: 'var(--green)', flexShrink: 0 }} />
                      <span style={{ fontWeight: 500, fontFamily: 'monospace', fontSize: 12 }}>{exp.filename}</span>
                    </div>
                  </td>
                  <td style={{ fontWeight: 700, color: 'var(--accent)' }}>{exp.row_count.toLocaleString()}</td>
                  <td>
                    <span style={{
                      fontWeight: 700,
                      color: exp.avg_match_score >= 70 ? 'var(--green)'
                           : exp.avg_match_score >= 40 ? 'var(--amber)'
                           : 'var(--red)'
                    }}>
                      {exp.avg_match_score.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {format(new Date(exp.created_at), 'MMM d, yyyy HH:mm')}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        className="btn btn-green btn-sm"
                        onClick={() => handleDownload(exp)}
                        disabled={downloadingId === exp.id}
                        title="Download Excel"
                      >
                        {downloadingId === exp.id ? (
                          <div className="spinner" style={{ width: 13, height: 13 }} />
                        ) : (
                          <Download size={13} />
                        )}
                        {downloadingId === exp.id ? 'Downloading...' : 'Download'}
                      </button>
                      <button
                        className="btn btn-danger btn-icon btn-sm"
                        onClick={() => handleDelete(exp.id)}
                        disabled={deleting === exp.id}
                        title="Delete export"
                      >
                        {deleting === exp.id ? <div className="spinner" style={{ width: 12, height: 12 }} /> : <Trash2 size={13} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <GenerateModal
          onClose={() => setShowModal(false)}
          onDone={() => { setShowModal(false); load() }}
        />
      )}
    </>
  )
}
