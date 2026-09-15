import React, { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import type { FilterConfig, FilterConfigUpdate } from '../types'
import { Save, Plus, X, AlertTriangle, SlidersHorizontal } from 'lucide-react'

// Reusable editable tag-list with input
function TagEditor({
  label, values, onChange, placeholder
}: { label: string; values: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  const [input, setInput] = useState('')
  const add = () => {
    const v = input.trim()
    if (v && !values.includes(v)) onChange([...values, v])
    setInput('')
  }
  return (
    <div className="form-group">
      <label className="label">{label}</label>
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          className="input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder ?? 'Add value…'}
        />
        <button type="button" className="btn btn-ghost btn-sm" onClick={add}>
          <Plus size={13} />
        </button>
      </div>
      {values.length > 0 && (
        <div className="tag-list" style={{ marginTop: 8 }}>
          {values.map(v => (
            <span
              key={v}
              className="tag removable"
              onClick={() => onChange(values.filter(x => x !== v))}
            >
              {v}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function FiltersPage() {
  const [config, setConfig] = useState<FilterConfig | null>(null)
  const [form, setForm] = useState<FilterConfigUpdate>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<FilterConfig>('/filters')
      setConfig(data)
      setForm({
        target_locations: data.target_locations,
        backend_keywords: data.backend_keywords,
        exclude_keywords: data.exclude_keywords,
        tech_stack_keywords: data.tech_stack_keywords,
        min_experience: data.min_experience,
        max_experience: data.max_experience,
        llm_suggestion_threshold: data.llm_suggestion_threshold,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const set = (k: keyof FilterConfigUpdate, v: any) => setForm(f => ({ ...f, [k]: v }))

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSaved(false)
    try {
      await api.put('/filters', form)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to save filter config')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="page-spinner"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
  }

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Filters</h1>
            <p className="page-subtitle">Configure scraping and ranking rules without redeploying code</p>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {saved && <span className="badge badge-green">✓ Saved</span>}
            <button id="save-filters-btn" className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Save size={14} />}
              Save Config
            </button>
          </div>
        </div>
      </div>

      <div className="page-body">
        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}><AlertTriangle size={15} />{error}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, maxWidth: 1100 }}>
          {/* Experience range */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <SlidersHorizontal size={16} style={{ color: 'var(--accent)' }} />
              <span style={{ fontWeight: 700 }}>Experience Range</span>
            </div>
            <div className="grid-2" style={{ gap: 12 }}>
              <div className="form-group">
                <label className="label">Min Years</label>
                <input
                  type="number" min={0} max={20} className="input"
                  value={form.min_experience ?? 0}
                  onChange={e => set('min_experience', parseInt(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label className="label">Max Years</label>
                <input
                  type="number" min={0} max={20} className="input"
                  value={form.max_experience ?? 3}
                  onChange={e => set('max_experience', parseInt(e.target.value))}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginTop: 14 }}>
              <label className="label">LLM Suggestion Threshold (%)</label>
              <input
                type="range" min={0} max={100}
                value={form.llm_suggestion_threshold ?? 60}
                onChange={e => set('llm_suggestion_threshold', parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent)' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                <span>0%</span>
                <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{form.llm_suggestion_threshold ?? 60}%</span>
                <span>100%</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>
                Jobs above this score threshold receive AI-generated resume bullet suggestions
              </div>
            </div>
          </div>

          {/* Target locations */}
          <div className="card">
            <TagEditor
              label="Target Locations"
              values={form.target_locations ?? []}
              onChange={v => set('target_locations', v)}
              placeholder="e.g. Bangalore, Remote, Hyderabad"
            />
          </div>

          {/* Backend keywords */}
          <div className="card">
            <TagEditor
              label="Backend Keywords (require match in title/JD)"
              values={form.backend_keywords ?? []}
              onChange={v => set('backend_keywords', v)}
              placeholder="e.g. backend, api, microservices"
            />
          </div>

          {/* Exclude keywords */}
          <div className="card">
            <TagEditor
              label="Exclude Keywords (disqualify if found)"
              values={form.exclude_keywords ?? []}
              onChange={v => set('exclude_keywords', v)}
              placeholder="e.g. frontend, react, mobile"
            />
          </div>

          {/* Tech stack */}
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <TagEditor
              label="Tech Stack Keywords (boost match score)"
              values={form.tech_stack_keywords ?? []}
              onChange={v => set('tech_stack_keywords', v)}
              placeholder="e.g. Python, Go, Kubernetes, PostgreSQL"
            />
          </div>
        </div>

        {config && (
          <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-muted)' }}>
            Config ID: {config.id} · Last updated: {new Date(config.updated_at).toLocaleString()}
          </div>
        )}
      </div>
    </>
  )
}
