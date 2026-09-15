import React, { useEffect, useState } from 'react'
import api from '../api/client'
import type { JobStats, ScrapeRun } from '../types'
import { format } from 'date-fns'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import { TrendingUp, Users, Award, AlertCircle, Zap, Code2 } from 'lucide-react'

export default function OverviewPage() {
  const [stats, setStats] = useState<JobStats | null>(null)
  const [runs, setRuns] = useState<ScrapeRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<JobStats>('/jobs/stats'),
      api.get<{ items: ScrapeRun[]; total: number }>('/runs?page=1&page_size=7')
    ]).then(([statsRes, runsRes]) => {
      setStats(statsRes.data)
      setRuns(runsRes.data.items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="page-spinner">
        <div className="spinner" style={{ width: 36, height: 36 }} />
      </div>
    )
  }

  const skillData = Object.entries(stats?.top_demanded_skills ?? {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([name, count]) => ({ name, count }))

  const latestRun = runs[0]

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Overview</h1>
            <p className="page-subtitle">Real-time pipeline health and job lead statistics</p>
          </div>
          {latestRun && (
            <span className={`badge ${latestRun.status === 'completed' ? 'badge-green' : latestRun.status === 'running' ? 'badge-accent' : 'badge-red'}`}>
              Last run: {format(new Date(latestRun.started_at), 'MMM d, HH:mm')}
            </span>
          )}
        </div>
      </div>

      <div className="page-body">
        {/* Stats grid */}
        <div className="grid-4" style={{ marginBottom: 24 }}>
          <div className="stat-card accent">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <TrendingUp size={18} style={{ color: 'var(--accent)' }} />
              <span className="stat-label">Total Leads</span>
            </div>
            <div className="stat-value">{(stats?.total_leads ?? 0).toLocaleString()}</div>
            <div className="stat-sub">{stats?.companies_represented ?? 0} companies</div>
          </div>

          <div className="stat-card green">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <Award size={18} style={{ color: 'var(--green)' }} />
              <span className="stat-label">High Match</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--green)' }}>{stats?.high_match_count ?? 0}</div>
            <div className="stat-sub">Score ≥ 70</div>
          </div>

          <div className="stat-card amber">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <Zap size={18} style={{ color: 'var(--amber)' }} />
              <span className="stat-label">Mid Match</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--amber)' }}>{stats?.mid_match_count ?? 0}</div>
            <div className="stat-sub">Score 40–69</div>
          </div>

          <div className="stat-card red">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <AlertCircle size={18} style={{ color: 'var(--red)' }} />
              <span className="stat-label">Low Match</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--red)' }}>{stats?.low_match_count ?? 0}</div>
            <div className="stat-sub">Score &lt; 40</div>
          </div>
        </div>

        <div className="grid-2" style={{ gap: 20 }}>
          {/* Top Skills chart */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <Code2 size={16} style={{ color: 'var(--accent)' }} />
              <span style={{ fontWeight: 700, fontSize: 14 }}>Top Demanded Skills</span>
            </div>
            {skillData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={skillData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                    labelStyle={{ color: 'var(--text-primary)' }}
                    cursor={{ fill: 'rgba(99,179,237,0.05)' }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {skillData.map((_, i) => (
                      <Cell key={i} fill={`hsl(${210 - i * 8}, 80%, ${60 - i * 2}%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">No skill data yet</div>
            )}
          </div>

          {/* Recent runs */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <Users size={16} style={{ color: 'var(--purple)' }} />
              <span style={{ fontWeight: 700, fontSize: 14 }}>Recent Scrape Runs</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {runs.length === 0 ? (
                <div className="empty-state">No runs recorded yet</div>
              ) : runs.map(run => (
                <div key={run.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg-raised)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {format(new Date(run.started_at), 'MMM d, HH:mm')}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {run.total_valid_leads} leads · {run.total_companies} companies · avg {run.avg_match_score.toFixed(0)}%
                    </div>
                  </div>
                  <span className={`badge ${
                    run.status === 'completed' ? 'badge-green'
                    : run.status === 'running'   ? 'badge-accent'
                    : 'badge-red'
                  }`}>
                    {run.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
