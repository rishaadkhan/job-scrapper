import React, { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import type { Export, ExportListResponse, ExportRequest } from '../types'
import { format } from 'date-fns'
import { Download, Trash2, Plus, FileSpreadsheet, AlertTriangle, X, Check } from 'lucide-react'

// ── Generate Export Modal ──────────────────────────────────
function GenerateModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState<ExportRequest>({ min_score: undefined, limit: 1000 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k: keyof ExportRequest, v: any) => setForm(f => ({ ...f, [k]: v || undefined }))

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
              <input type="number" min={0} max={100} className="input" placeholder="0 = all" value={form.min_score ?? ''} onChange={e => set('min_score', parseInt(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="label">Max Rows</label>
              <input type="number" min={1} max={5000} className="input" value={form.limit ?? 1000} onChange={e => set('limit', parseInt(e.target.value))} />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="label">Date From</label>
              <input type="date" className="input" value={form.date_from ?? ''} onChange={e => set('date_from', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="label">Date To</label>
              <input type="date" className="input" value={form.date_to ?? ''} onChange={e => set('date_to', e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="label">Filter by Company</label>
            <input className="input" placeholder="Leave blank for all" value={form.company ?? ''} onChange={e => set('company', e.target.value)} />
          </div>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 6 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
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

  const handleDownload = (exp: Export) => {
    // Open the download URL in a new tab — browser will prompt file download
    window.open(`/api${exp.download_url}`, '_blank')
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
                        title="Download Excel"
                      >
                        <Download size={13} /> Download
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
