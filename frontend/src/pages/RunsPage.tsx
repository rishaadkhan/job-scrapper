import React, { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import type { ScrapeRun, ScrapeRunListResponse } from '../types'
import { format, formatDuration, intervalToDuration } from 'date-fns'
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle size={15} style={{ color: 'var(--green)' }} />
  if (status === 'running')   return <Loader2 size={15} style={{ color: 'var(--accent)', animation: 'spin 1s linear infinite' }} />
  return <XCircle size={15} style={{ color: 'var(--red)' }} />
}

function duration(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

export default function RunsPage() {
  const [data, setData] = useState<ScrapeRunListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)
  const PAGE_SIZE = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data: res } = await api.get<ScrapeRunListResponse>(`/runs?page=${page}&page_size=${PAGE_SIZE}`)
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { load() }, [load])

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE)

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Scrape Runs</h1>
          <p className="page-subtitle">{data?.total ?? '…'} historical runs · pipeline execution history</p>
        </div>
      </div>

      <div className="page-body">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Started</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Companies</th>
                <th>Raw Jobs</th>
                <th>Valid Leads</th>
                <th>Avg Score</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr><td colSpan={8}><div className="empty-state">No runs recorded yet</div></td></tr>
              ) : (data?.items ?? []).map(run => (
                <React.Fragment key={run.id}>
                  <tr
                    style={{ cursor: run.error_log ? 'pointer' : 'default' }}
                    onClick={() => run.error_log && setExpanded(e => e === run.id ? null : run.id)}
                  >
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
                      {duration(run.duration_sec)}
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
                  </tr>
                  {expanded === run.id && run.error_log && (
                    <tr>
                      <td colSpan={8} style={{ background: 'var(--bg-raised)', padding: '12px 20px' }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--red)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Error Log</div>
                        <pre style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                          {run.error_log}
                        </pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
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
    </>
  )
}
