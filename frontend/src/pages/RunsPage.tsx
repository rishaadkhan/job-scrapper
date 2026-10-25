import { useEffect, useState, useCallback, useRef, Fragment } from 'react'
import api from '../api/client'
import type { ScrapeRunListResponse, ScrapeRun } from '../types'
import { format } from 'date-fns'
import {
  CheckCircle, XCircle, Loader2, Play, RefreshCw, AlertCircle,
  CheckCircle2, X, Download, Trash2
} from 'lucide-react'
import ConfirmModal from '../components/ConfirmModal'

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle size={15} style={{ color: 'var(--green)' }} />
  if (status === 'running')   return <Loader2 size={15} style={{ color: 'var(--accent)', animation: 'spin 1s linear infinite' }} />
  return <XCircle size={15} style={{ color: 'var(--red)' }} />
}

function duration(sec: number, status: string): string {
  if (status === 'running') return 'In progress…'
  if (sec < 60) return `${Math.round(sec)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

export default function RunsPage() {
  const [data, setData] = useState<ScrapeRunListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [alert, setAlert] = useState<{ type: 'info' | 'warn' | 'error'; message: string } | null>(null)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [bulkDownloading, setBulkDownloading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const headerCheckboxRef = useRef<HTMLInputElement>(null)
  const PAGE_SIZE = 20

  const load = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true)
    try {
      const { data: res } = await api.get<ScrapeRunListResponse>(`/runs?page=${page}&page_size=${PAGE_SIZE}`)
      setData(res)
    } finally {
      if (!isSilent) setLoading(false)
    }
  }, [page])

  useEffect(() => { load() }, [load])

  // Detect if any scrape run is actively executing
  const hasActiveRun = data?.items.some(r => r.status === 'running') ?? false

  // Auto-poll every 4 seconds while any run is in 'running' state
  useEffect(() => {
    if (!hasActiveRun) return
    const interval = setInterval(() => {
      load(true)
    }, 4000)
    return () => clearInterval(interval)
  }, [hasActiveRun, load])

  // Selection calculations
  const currentRunIds = (data?.items ?? []).map(r => r.id)
  const isAllSelected = currentRunIds.length > 0 && currentRunIds.every(id => selectedIds.includes(id))
  const isSomeSelected = selectedIds.length > 0 && !isAllSelected

  useEffect(() => {
    if (headerCheckboxRef.current) {
      headerCheckboxRef.current.indeterminate = isSomeSelected
    }
  }, [isSomeSelected])

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedIds(prev => prev.filter(id => !currentRunIds.includes(id)))
    } else {
      setSelectedIds(prev => Array.from(new Set([...prev, ...currentRunIds])))
    }
  }

  const toggleSelectRow = (id: number) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const clearSelection = () => setSelectedIds([])

  const handleTriggerRun = async () => {
    if (!window.confirm("Trigger a full scraping, filtering, and scoring run in the background across all active companies?")) {
      return
    }

    setTriggering(true)
    setAlert(null)
    try {
      const res = await api.post<{ message: string; run_id: number; status: string }>('/runs/trigger')
      setAlert({
        type: 'info',
        message: `${res.data.message} (Run #${res.data.run_id}). Live status will update automatically.`
      })
      await load()
    } catch (err: any) {
      setAlert({
        type: 'error',
        message: err?.response?.data?.detail ?? 'Failed to initiate scrape run.'
      })
    } finally {
      setTriggering(false)
    }
  }

  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean
    ids: number[]
    label: string
  }>({
    isOpen: false,
    ids: [],
    label: ''
  })

  const promptDeleteOne = (run: ScrapeRun) => {
    setDeleteModal({
      isOpen: true,
      ids: [run.id],
      label: `Scrape Run #${run.id}`
    })
  }

  const promptBulkDelete = () => {
    if (selectedIds.length === 0) return
    setDeleteModal({
      isOpen: true,
      ids: selectedIds,
      label: `${selectedIds.length} scrape run(s)`
    })
  }

  const handleConfirmDelete = async () => {
    if (deleteModal.ids.length === 0) return
    setBulkDeleting(true)
    setAlert(null)
    try {
      if (deleteModal.ids.length === 1) {
        const id = deleteModal.ids[0]
        setDeletingId(id)
        await api.delete(`/runs/${id}`)
        setSelectedIds(prev => prev.filter(x => x !== id))
        setAlert({ type: 'info', message: `Scrape run #${id} successfully deleted.` })
      } else {
        const res = await api.post<{ message: string; affected_count: number }>('/runs/bulk-delete', { ids: deleteModal.ids })
        setAlert({ type: 'info', message: res.data.message })
        setSelectedIds(prev => prev.filter(id => !deleteModal.ids.includes(id)))
      }
      setDeleteModal({ isOpen: false, ids: [], label: '' })
      await load()
    } catch (err: any) {
      console.error('Delete run failed:', err)
      setAlert({
        type: 'error',
        message: err?.response?.data?.detail ?? 'Failed to delete scrape run(s).'
      })
    } finally {
      setBulkDeleting(false)
      setDeletingId(null)
    }
  }

  const handleDownloadRun = async (run: ScrapeRun) => {
    setDownloadingId(run.id)
    try {
      const res = await api.get(`/runs/${run.id}/download`, { responseType: 'blob' })
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `scrape_run_${run.id}_report.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Download failed:', err)
      setAlert({
        type: 'error',
        message: err?.response?.data?.detail ?? 'Failed to download scrape run report.'
      })
    } finally {
      setDownloadingId(null)
    }
  }

  const handleBulkDownload = async () => {
    if (selectedIds.length === 0) return
    setBulkDownloading(true)
    try {
      const res = await api.post('/runs/bulk-download', { ids: selectedIds }, { responseType: 'blob' })
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const filename = selectedIds.length === 1
        ? `scrape_run_${selectedIds[0]}_report.xlsx`
        : `scrape_runs_report_${format(new Date(), 'yyyyMMdd_HHmmss')}.xlsx`
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Bulk download failed:', err)
      setAlert({
        type: 'error',
        message: err?.response?.data?.detail ?? 'Failed to download selected scrape runs report.'
      })
    } finally {
      setBulkDownloading(false)
    }
  }

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE)

  return (
    <>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 className="page-title">Scrape Runs</h1>
            <p className="page-subtitle">{data?.total ?? '…'} historical runs · pipeline execution history</p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => load()}
              disabled={loading}
              title="Refresh telemetry"
            >
              <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
            <button
              id="trigger-run-btn"
              className="btn btn-primary"
              onClick={handleTriggerRun}
              disabled={triggering || hasActiveRun}
              title={hasActiveRun ? "A scrape run is currently in progress" : "Launch scrape pipeline now"}
            >
              {triggering || hasActiveRun ? (
                <>
                  <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
                  {hasActiveRun ? 'Scraper In Progress…' : 'Initiating…'}
                </>
              ) : (
                <>
                  <Play size={15} />
                  Run Scraper Now
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="page-body">
        {alert && (
          <div
            className={`alert alert-${alert.type}`}
            style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {alert.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
              <span>{alert.message}</span>
            </div>
            <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setAlert(null)}>
              <X size={14} />
            </button>
          </div>
        )}

        {hasActiveRun && !alert && (
          <div className="alert alert-info" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
            <span>A scrape pipeline is currently running. Telemetry and leads are refreshing automatically.</span>
          </div>
        )}

        {/* Bulk Action Bar */}
        {selectedIds.length > 0 && (
          <div className="bulk-actions-bar">
            <div className="bulk-count">
              <span className="bulk-badge">{selectedIds.length}</span>
              <span>{selectedIds.length === 1 ? '1 run selected' : `${selectedIds.length} runs selected`}</span>
            </div>
            <div className="bulk-btns">
              <button
                id="bulk-download-runs-btn"
                className="btn btn-green btn-sm"
                onClick={handleBulkDownload}
                disabled={bulkDownloading}
                title="Download report for selected runs"
              >
                {bulkDownloading ? (
                  <div className="spinner" style={{ width: 13, height: 13 }} />
                ) : (
                  <Download size={13} />
                )}
                {bulkDownloading ? 'Generating Report…' : 'Download Report (.xlsx)'}
              </button>
              <button
                id="bulk-delete-runs-btn"
                className="btn btn-danger btn-sm"
                onClick={promptBulkDelete}
                disabled={bulkDeleting}
                title="Delete selected scrape runs"
              >
                {bulkDeleting ? (
                  <div className="spinner" style={{ width: 13, height: 13 }} />
                ) : (
                  <Trash2 size={13} />
                )}
                {bulkDeleting ? 'Deleting…' : 'Delete Selected'}
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
                    aria-label="Select all runs on this page"
                    title={isAllSelected ? "Deselect all on this page" : "Select all runs on this page"}
                  />
                </th>
                <th>#</th>
                <th>Started</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Companies</th>
                <th>Raw Jobs</th>
                <th>Valid Leads</th>
                <th>Avg Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && !data ? (
                <tr><td colSpan={10} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <div className="empty-state">
                      <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 6 }}>No runs recorded yet</div>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16, maxWidth: 420 }}>
                        Trigger your first ingestion pipeline to fetch, filter, and score live job openings across configured company portals.
                      </p>
                      <button
                        className="btn btn-primary"
                        onClick={handleTriggerRun}
                        disabled={triggering || hasActiveRun}
                      >
                        <Play size={14} /> Run First Scrape Now
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (data?.items ?? []).map(run => {
                const isSelected = selectedIds.includes(run.id)
                return (
                  <Fragment key={run.id}>
                    <tr
                      className={isSelected ? 'selected-row' : ''}
                      style={{ cursor: run.error_log ? 'pointer' : 'default' }}
                      onClick={() => run.error_log && setExpanded(e => e === run.id ? null : run.id)}
                    >
                      <td className="checkbox-cell" onClick={e => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          className="custom-checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectRow(run.id)}
                          aria-label={`Select run #${run.id}`}
                        />
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: 12 }}>#{run.id}</td>
                      <td>
                        <div style={{ fontWeight: 600, fontSize: 13 }}>{format(new Date(run.started_at), 'MMM d, yyyy')}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{format(new Date(run.started_at), 'HH:mm:ss')}</div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <StatusIcon status={run.status} />
                          <span className={`badge ${
                            run.status === 'completed' ? 'badge-green'
                            : run.status === 'running' ? 'badge-accent'
                            : 'badge-red'
                          }`}>{run.status}</span>
                        </div>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-secondary)' }}>
                        {duration(run.duration_sec, run.status)}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{run.companies_with_jobs}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>/{run.total_companies}</span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{run.total_raw_jobs.toLocaleString()}</td>
                      <td style={{ color: 'var(--accent)', fontWeight: 700 }}>{run.total_valid_leads}</td>
                      <td>
                        <span style={{
                          fontWeight: 700, fontSize: 13,
                          color: run.avg_match_score >= 70 ? 'var(--green)'
                               : run.avg_match_score >= 40 ? 'var(--amber)'
                               : 'var(--red)'
                        }}>
                          {run.avg_match_score.toFixed(1)}%
                        </span>
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <div className="flex gap-2">
                          <button
                            className="btn btn-ghost btn-sm btn-icon"
                            onClick={(e) => { e.stopPropagation(); handleDownloadRun(run) }}
                            disabled={downloadingId === run.id}
                            title="Download run report (.xlsx)"
                          >
                            {downloadingId === run.id ? (
                              <div className="spinner" style={{ width: 12, height: 12 }} />
                            ) : (
                              <Download size={13} style={{ color: 'var(--green)' }} />
                            )}
                          </button>
                          <button
                            className="btn btn-danger btn-icon btn-sm"
                            onClick={(e) => { e.stopPropagation(); promptDeleteOne(run) }}
                            disabled={deletingId === run.id || run.status === 'running'}
                            title={run.status === 'running' ? "Cannot delete active run" : "Delete run"}
                          >
                            {deletingId === run.id ? (
                              <div className="spinner" style={{ width: 12, height: 12 }} />
                            ) : (
                              <Trash2 size={13} />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                    {expanded === run.id && run.error_log && (
                      <tr>
                        <td colSpan={10} style={{ background: 'var(--bg-raised)', padding: '12px 20px' }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--red)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Error Log</div>
                          <pre style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                            {run.error_log}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '0 8px' }}>Page {page} / {totalPages}</span>
            <button className="btn btn-ghost btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        )}
      </div>

      <ConfirmModal
        isOpen={deleteModal.isOpen}
        title={deleteModal.ids.length === 1 ? 'Delete Scrape Run' : 'Delete Selected Scrape Runs'}
        message={`Are you sure you want to permanently delete ${deleteModal.label}? All related execution logs and metrics will be removed.`}
        confirmText={deleteModal.ids.length === 1 ? 'Delete Run' : `Delete (${deleteModal.ids.length})`}
        loading={bulkDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => !bulkDeleting && setDeleteModal({ isOpen: false, ids: [], label: '' })}
      />
    </>
  )
}
