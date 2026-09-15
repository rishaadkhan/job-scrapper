import React, { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import type { Job, JobListResponse } from '../types'
import { Search, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? 'var(--green)' : score >= 40 ? 'var(--amber)' : 'var(--red)'
  return (
    <div className="score-bar">
      <div className="score-track">
        <div className="score-fill" style={{ width: `${score}%`, background: color }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 30 }}>{score}</span>
    </div>
  )
}

function JobRow({ job }: { job: Job }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr style={{ cursor: 'pointer' }} onClick={() => setExpanded(e => !e)}>
        <td>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{job.title}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{job.company_name}</div>
        </td>
        <td><ScoreBar score={job.match_score} /></td>
        <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{job.location ?? '—'}</td>
        <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{job.experience_range ?? '—'}</td>
        <td>
          <div className="tag-list">
            {(job.top_jd_keywords ?? []).slice(0, 3).map(k => (
              <span key={k} className="badge badge-accent" style={{ fontSize: 10 }}>{k}</span>
            ))}
            {(job.top_jd_keywords ?? []).length > 3 && (
              <span className="badge badge-muted" style={{ fontSize: 10 }}>+{job.top_jd_keywords.length - 3}</span>
            )}
          </div>
        </td>
        <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {job.posted_date ? new Date(job.posted_date).toLocaleDateString() : '—'}
        </td>
        <td>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {job.apply_link && (
              <a
                href={job.apply_link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost btn-icon btn-sm"
                onClick={e => e.stopPropagation()}
                title="Apply"
              >
                <ExternalLink size={12} />
              </a>
            )}
            {expanded ? <ChevronUp size={14} style={{ color: 'var(--text-muted)' }} /> : <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />}
          </div>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={7} style={{ background: 'var(--bg-raised)', padding: '16px 20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {job.missing_from_resume && job.missing_from_resume.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Missing from Resume</div>
                  <div className="tag-list">
                    {job.missing_from_resume.map(k => <span key={k} className="badge badge-red" style={{ fontSize: 10 }}>{k}</span>)}
                  </div>
                </div>
              )}
              {job.suggested_bullets && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Suggested Resume Bullets</div>
                  <pre style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                    {job.suggested_bullets}
                  </pre>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function JobsPage() {
  const [data, setData] = useState<JobListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [company, setCompany] = useState('')
  const [minScore, setMinScore] = useState('')
  const [loading, setLoading] = useState(true)

  const PAGE_SIZE = 30

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
      if (company) params.set('company', company)
      if (minScore) params.set('min_score', minScore)
      const { data: res } = await api.get<JobListResponse>(`/jobs?${params}`)
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [page, company, minScore])

  useEffect(() => { load() }, [load])

  // Debounce company search
  useEffect(() => {
    const t = setTimeout(() => { setCompany(searchInput); setPage(1) }, 400)
    return () => clearTimeout(t)
  }, [searchInput])

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE)

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Job Leads</h1>
            <p className="page-subtitle">{data?.total ?? '…'} leads · click a row to expand details</p>
          </div>
        </div>
      </div>

      <div className="page-body">
        {/* Filter bar */}
        <div className="card-sm flex items-center gap-3" style={{ marginBottom: 16 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input id="jobs-search" className="input" style={{ paddingLeft: 32 }} placeholder="Filter by company…" value={searchInput} onChange={e => setSearchInput(e.target.value)} />
          </div>
          <select className="input" style={{ width: 160 }} value={minScore} onChange={e => { setMinScore(e.target.value); setPage(1) }}>
            <option value="">All scores</option>
            <option value="70">High (70+)</option>
            <option value="40">Mid+ (40+)</option>
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title / Company</th>
                <th style={{ minWidth: 130 }}>Match Score</th>
                <th>Location</th>
                <th>Experience</th>
                <th>Top Skills</th>
                <th>Posted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr><td colSpan={7}><div className="empty-state">No job leads found</div></td></tr>
              ) : (data?.items ?? []).map(job => (
                <JobRow key={job.id} job={job} />
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
