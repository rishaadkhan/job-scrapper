import React, { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import type { Company, CompanyListResponse, CompanyCreate, CompanyUpdate } from '../types'
import { Plus, Search, Edit2, Trash2, AlertTriangle, X, Check } from 'lucide-react'

const ATS_OPTIONS = ['greenhouse', 'lever', 'ashby', 'smartrecruiters', 'workday', 'html_fallback']
const COMPANY_TYPES = ['Tech', 'Fintech', 'SaaS', 'E-commerce', 'Startup', 'Enterprise', 'Other']

// ── Company Form Modal ─────────────────────────────────────
interface CompanyModalProps {
  company?: Company | null
  onClose: () => void
  onSave: () => void
}

function CompanyModal({ company, onClose, onSave }: CompanyModalProps) {
  const editing = !!company
  const [form, setForm] = useState<CompanyCreate>({
    name: company?.name ?? '',
    career_url: company?.career_url ?? '',
    portal_type: company?.portal_type ?? 'generic',
    ats: company?.ats ?? 'html_fallback',
    ats_token: company?.ats_token ?? '',
    ats_id: company?.ats_id ?? '',
    location_filter: company?.location_filter ?? [],
    company_type: company?.company_type ?? 'Tech',
    active: company?.active ?? true,
  })
  const [locationInput, setLocationInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k: keyof CompanyCreate, v: any) => setForm(f => ({ ...f, [k]: v }))

  const addLocation = () => {
    const v = locationInput.trim()
    if (v && !form.location_filter?.includes(v)) {
      set('location_filter', [...(form.location_filter ?? []), v])
    }
    setLocationInput('')
  }

  const removeLocation = (loc: string) =>
    set('location_filter', form.location_filter?.filter(l => l !== loc) ?? [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { ...form, ats_token: form.ats_token || null, ats_id: form.ats_id || null }
      if (editing) {
        await api.put(`/companies/${company!.id}`, payload)
      } else {
        await api.post('/companies', payload)
      }
      onSave()
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to save company')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">{editing ? 'Edit Company' : 'Add Company'}</span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 14 }}><AlertTriangle size={15} />{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="grid-2">
            <div className="form-group">
              <label className="label">Company Name *</label>
              <input className="input" value={form.name} onChange={e => set('name', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="label">Type</label>
              <select className="input" value={form.company_type} onChange={e => set('company_type', e.target.value)}>
                {COMPANY_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="label">Career URL *</label>
            <input className="input" type="url" value={form.career_url} onChange={e => set('career_url', e.target.value)} required placeholder="https://…" />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="label">ATS Platform</label>
              <select className="input" value={form.ats} onChange={e => set('ats', e.target.value)}>
                {ATS_OPTIONS.map(a => <option key={a}>{a}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="label">Portal Type</label>
              <input className="input" value={form.portal_type} onChange={e => set('portal_type', e.target.value)} placeholder="generic" />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="label">ATS Token / Board Slug</label>
              <input className="input" value={form.ats_token ?? ''} onChange={e => set('ats_token', e.target.value)} placeholder="optional" />
            </div>
            <div className="form-group">
              <label className="label">ATS Company ID</label>
              <input className="input" value={form.ats_id ?? ''} onChange={e => set('ats_id', e.target.value)} placeholder="optional" />
            </div>
          </div>

          {/* Location filter tags */}
          <div className="form-group">
            <label className="label">Location Filters</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                className="input"
                value={locationInput}
                onChange={e => setLocationInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addLocation())}
                placeholder="e.g. Bangalore, Remote"
              />
              <button type="button" className="btn btn-ghost btn-sm" onClick={addLocation}>Add</button>
            </div>
            {(form.location_filter ?? []).length > 0 && (
              <div className="tag-list" style={{ marginTop: 8 }}>
                {form.location_filter!.map(loc => (
                  <span key={loc} className="tag removable" onClick={() => removeLocation(loc)}>{loc}</span>
                ))}
              </div>
            )}
          </div>

          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <input id="active-toggle" type="checkbox" checked={form.active} onChange={e => set('active', e.target.checked)} />
            <label htmlFor="active-toggle" style={{ fontSize: 13, color: 'var(--text-secondary)', cursor: 'pointer' }}>
              Active (include in scraping runs)
            </label>
          </div>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 6 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Check size={14} />}
              {editing ? 'Save Changes' : 'Add Company'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────
export default function CompaniesPage() {
  const [data, setData] = useState<CompanyListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [atsFilter, setAtsFilter] = useState('')
  const [activeOnly, setActiveOnly] = useState(true)
  const [loading, setLoading] = useState(true)
  const [modalCompany, setModalCompany] = useState<Company | null | 'new'>('new' as any)
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Company | null>(null)

  const PAGE_SIZE = 50

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
        active_only: String(activeOnly),
      })
      if (search) params.set('search', search)
      if (atsFilter) params.set('ats', atsFilter)
      const { data: res } = await api.get<CompanyListResponse>(`/companies?${params}`)
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [page, search, atsFilter, activeOnly])

  useEffect(() => { load() }, [load])

  // Debounce search
  const [searchInput, setSearchInput] = useState('')
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1) }, 400)
    return () => clearTimeout(t)
  }, [searchInput])

  const handleDelete = async (id: number, hard = false) => {
    if (!confirm(hard ? 'Permanently delete this company?' : 'Deactivate this company?')) return
    await api.delete(`/companies/${id}?hard=${hard}`)
    load()
  }

  const atsBadge = (ats: string) => {
    const map: Record<string, string> = {
      greenhouse: 'badge-green', lever: 'badge-accent',
      ashby: 'badge-purple', smartrecruiters: 'badge-amber',
      workday: 'badge-amber', html_fallback: 'badge-muted'
    }
    return map[ats] ?? 'badge-muted'
  }

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE)

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Companies</h1>
            <p className="page-subtitle">{data?.total ?? '…'} companies · manage ATS targets and scraping config</p>
          </div>
          <button className="btn btn-primary" id="add-company-btn" onClick={() => { setEditTarget(null); setShowModal(true) }}>
            <Plus size={15} /> Add Company
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* Dedup warnings */}
        {(data?.dedup_warnings ?? []).length > 0 && (
          <div className="alert alert-warn" style={{ marginBottom: 16 }}>
            <AlertTriangle size={16} style={{ flexShrink: 0 }} />
            <div>
              <strong>Near-duplicate names detected:</strong>{' '}
              {data!.dedup_warnings.join(' · ')}
            </div>
          </div>
        )}

        {/* Filters bar */}
        <div className="card-sm flex items-center gap-3" style={{ marginBottom: 16 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input id="companies-search" className="input" style={{ paddingLeft: 32 }} placeholder="Search companies…" value={searchInput} onChange={e => setSearchInput(e.target.value)} />
          </div>
          <select className="input" style={{ width: 160 }} value={atsFilter} onChange={e => { setAtsFilter(e.target.value); setPage(1) }}>
            <option value="">All ATS</option>
            {ATS_OPTIONS.map(a => <option key={a}>{a}</option>)}
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'nowrap', cursor: 'pointer' }}>
            <input type="checkbox" checked={activeOnly} onChange={e => { setActiveOnly(e.target.checked); setPage(1) }} />
            Active only
          </label>
        </div>

        {/* Table */}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>ATS</th>
                <th>Type</th>
                <th>Jobs</th>
                <th>Last Scraped</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : (data?.items ?? []).length === 0 ? (
                <tr><td colSpan={7}><div className="empty-state">No companies found</div></td></tr>
              ) : (data?.items ?? []).map(c => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{c.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.career_url}
                    </div>
                  </td>
                  <td><span className={`badge ${atsBadge(c.ats)}`}>{c.ats}</span></td>
                  <td><span className="badge badge-muted">{c.company_type}</span></td>
                  <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{c.job_count}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                    {c.last_scraped_at ? new Date(c.last_scraped_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <span className={`badge ${c.active ? 'badge-green' : 'badge-muted'}`}>
                      {c.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-ghost btn-icon btn-sm" title="Edit" onClick={() => { setEditTarget(c); setShowModal(true) }}>
                        <Edit2 size={13} />
                      </button>
                      <button className="btn btn-danger btn-icon btn-sm" title="Deactivate" onClick={() => handleDelete(c.id)}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '0 8px' }}>Page {page} / {totalPages}</span>
            <button className="btn btn-ghost btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        )}
      </div>

      {showModal && (
        <CompanyModal
          company={editTarget}
          onClose={() => setShowModal(false)}
          onSave={() => { setShowModal(false); load() }}
        />
      )}
    </>
  )
}
