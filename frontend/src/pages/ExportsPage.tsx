import React, { useEffect, useState, useCallback, useRef } from 'react'
import api from '../api/client'
import type { Export, ExportListResponse, ExportRequest, JobListResponse } from '../types'
import { format } from 'date-fns'
import { Download, Trash2, Plus, FileSpreadsheet, AlertTriangle, X, RotateCcw } from 'lucide-react'
import ConfirmModal from '../components/ConfirmModal'

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
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkDownloading, setBulkDownloading] = useState(false)
  const [alertMessage, setAlertMessage] = useState<{ type: 'info' | 'warn' | 'error'; message: string } | null>(null)

  const headerCheckboxRef = useRef<HTMLInputElement>(null)

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

  // Selection state calculations
  const allIds = data?.items.map(e => e.id) ?? []
  const isAllSelected = allIds.length > 0 && allIds.every(id => selectedIds.includes(id))
  const isSomeSelected = selectedIds.length > 0 && !isAllSelected

  useEffect(() => {
    if (headerCheckboxRef.current) {
      headerCheckboxRef.current.indeterminate = isSomeSelected
    }
  }, [isSomeSelected])

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedIds([])
    } else {
      setSelectedIds(allIds)
    }
  }

  const toggleSelectRow = (id: number) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const clearSelection = () => setSelectedIds([])

  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean
    ids: number[]
    label: string
  }>({
    isOpen: false,
    ids: [],
    label: ''
  })

  const promptDeleteOne = (exp: Export) => {
    setDeleteModal({
      isOpen: true,
      ids: [exp.id],
      label: `"${exp.filename}"`
    })
  }

  const promptBulkDelete = () => {
    if (selectedIds.length === 0) return
    setDeleteModal({
      isOpen: true,
      ids: selectedIds,
      label: `${selectedIds.length} export spreadsheet(s)`
    })
  }

  const handleConfirmDelete = async () => {
    if (deleteModal.ids.length === 0) return
    setBulkLoading(true)
    setAlertMessage(null)
    try {
      if (deleteModal.ids.length === 1) {
        const id = deleteModal.ids[0]
        await api.delete(`/exports/${id}`)
        setSelectedIds(prev => prev.filter(x => x !== id))
        setAlertMessage({ type: 'info', message: 'Export spreadsheet successfully deleted.' })
      } else {
        const res = await api.post<{ message: string; affected_count: number }>('/exports/bulk-delete', { ids: deleteModal.ids })
        setAlertMessage({ type: 'info', message: res.data.message })
        setSelectedIds(prev => prev.filter(id => !deleteModal.ids.includes(id)))
      }
      setDeleteModal({ isOpen: false, ids: [], label: '' })
      await load()
    } catch (err: any) {
      console.error('Delete failed:', err)
      setAlertMessage({
        type: 'error',
        message: err?.response?.data?.detail ?? 'Failed to delete export(s).'
      })
    } finally {
      setBulkLoading(false)
    }
  }

  const handleDownload = async (exp: Export) => {
    setDownloadingId(exp.id)
    try {
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

  const handleBulkDownload = async () => {
    if (selectedIds.length === 0) return
    setBulkDownloading(true)
    try {
      const res = await api.post('/exports/bulk-download', { ids: selectedIds }, { responseType: 'blob' })
      const isZip = selectedIds.length > 1
      const defaultFilename = isZip
        ? `exports_bundle_${format(new Date(), 'yyyyMMdd_HHmmss')}.zip`
        : (data?.items.find(e => e.id === selectedIds[0])?.filename ?? 'export.xlsx')

      const contentType = isZip
        ? 'application/zip'
        : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

      const blob = new Blob([res.data], { type: contentType })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', defaultFilename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Bulk download failed:', err)
      alert(err?.response?.data?.detail ?? 'Failed to download selected exports.')
    } finally {
      setBulkDownloading(false)
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
        {/* Feedback alert */}
        {alertMessage && (
          <div
            className={`alert alert-${alertMessage.type}`}
            style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          >
            <span>{alertMessage.message}</span>
            <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setAlertMessage(null)}>
              <X size={14} />
            </button>
          </div>
        )}

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

        {/* Bulk Action Bar */}
        {selectedIds.length > 0 && (
          <div className="bulk-actions-bar">
            <div className="bulk-count">
              <span className="bulk-badge">{selectedIds.length}</span>
              <span>{selectedIds.length === 1 ? '1 export selected' : `${selectedIds.length} exports selected`}</span>
            </div>
            <div className="bulk-btns">
              <button
                id="bulk-download-btn"
                className="btn btn-green btn-sm"
                onClick={handleBulkDownload}
                disabled={bulkDownloading}
                title="Download selected exports"
              >
                {bulkDownloading ? (
                  <div className="spinner" style={{ width: 13, height: 13 }} />
                ) : (
                  <Download size={13} />
                )}
                {bulkDownloading ? 'Downloading…' : selectedIds.length > 1 ? 'Download Bundle (ZIP)' : 'Download Excel'}
              </button>
              <button
                id="bulk-delete-btn"
                className="btn btn-danger btn-sm"
                onClick={promptBulkDelete}
                disabled={bulkLoading}
                title="Delete selected exports"
              >
                {bulkLoading ? (
                  <div className="spinner" style={{ width: 13, height: 13 }} />
                ) : (
                  <Trash2 size={13} />
                )}
                {bulkLoading ? 'Deleting…' : 'Delete Selected'}
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={clearSelection}
                title="Deselect all"
              >
                <X size={13} /> Deselect
              </button>
            </div>
          </div>
        )}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className="checkbox-cell">
                  <input
                    ref={headerCheckboxRef}
                    type="checkbox"
                    className="custom-checkbox"
                    checked={isAllSelected}
                    onChange={toggleSelectAll}
                    aria-label="Select all exports"
                    title={isAllSelected ? "Deselect all" : "Select all exports"}
                  />
                </th>
                <th>Filename</th>
                <th>Rows</th>
                <th>Avg Score</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr><td colSpan={6}>
                  <div className="empty-state">
                    <FileSpreadsheet size={40} />
                    <div>No exports yet</div>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>Generate first export</button>
                  </div>
                </td></tr>
              ) : (data?.items ?? []).map(exp => {
                const isSelected = selectedIds.includes(exp.id)
                return (
                  <tr
                    key={exp.id}
                    className={isSelected ? 'selected-row' : ''}
                    style={{ cursor: 'pointer' }}
                    onClick={() => toggleSelectRow(exp.id)}
                  >
                    <td className="checkbox-cell" onClick={e => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="custom-checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelectRow(exp.id)}
                        aria-label={`Select ${exp.filename}`}
                      />
                    </td>
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
                    <td onClick={e => e.stopPropagation()}>
                      <div className="flex gap-2">
                        <button
                          className="btn btn-green btn-sm"
                          onClick={(e) => { e.stopPropagation(); handleDownload(exp) }}
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
                          onClick={(e) => { e.stopPropagation(); promptDeleteOne(exp) }}
                          disabled={bulkLoading}
                          title="Delete export"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
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

      <ConfirmModal
        isOpen={deleteModal.isOpen}
        title={deleteModal.ids.length === 1 ? 'Delete Export Spreadsheet' : 'Delete Selected Export Spreadsheets'}
        message={`Are you sure you want to permanently delete ${deleteModal.label}? This action will remove the spreadsheet from disk and database.`}
        loading={bulkLoading}
        onConfirm={handleConfirmDelete}
        onCancel={() => !bulkLoading && setDeleteModal({ isOpen: false, ids: [], label: '' })}
      />
    </>
  )
}
