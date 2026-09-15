// Shared TypeScript types mirroring backend Pydantic schemas

export interface TokenResponse {
  access_token: string
  token_type: string
  role: string
  email: string
}

export interface Company {
  id: number
  name: string
  career_url: string
  portal_type: string
  ats: string
  ats_token?: string | null
  ats_id?: string | null
  location_filter: string[]
  company_type: string
  active: boolean
  last_scraped_at?: string | null
  job_count: number
  created_at: string
  updated_at: string
}

export interface CompanyListResponse {
  items: Company[]
  total: number
  page: number
  page_size: number
  dedup_warnings: string[]
}

export interface CompanyCreate {
  name: string
  career_url: string
  portal_type?: string
  ats?: string
  ats_token?: string | null
  ats_id?: string | null
  location_filter?: string[]
  company_type?: string
  active?: boolean
}

export interface CompanyUpdate extends Partial<CompanyCreate> {}

export interface Job {
  id: number
  job_id: string
  company_name: string
  company_type?: string
  title: string
  match_score: number
  experience_range?: string
  location?: string
  top_jd_keywords: string[]
  missing_from_resume: string[]
  suggested_bullets?: string
  posted_date?: string
  apply_link?: string
  portal_url?: string
  description?: string
  stack_match: boolean
  scraped_at: string
  created_at: string
}

export interface JobListResponse {
  items: Job[]
  total: number
  page: number
  page_size: number
}

export interface JobStats {
  total_leads: number
  high_match_count: number
  mid_match_count: number
  low_match_count: number
  companies_represented: number
  top_demanded_skills: Record<string, number>
}

export interface FilterConfig {
  id: number
  name: string
  is_active: boolean
  target_locations: string[]
  backend_keywords: string[]
  exclude_keywords: string[]
  tech_stack_keywords: string[]
  min_experience: number
  max_experience: number
  llm_suggestion_threshold: number
  updated_at: string
}

export interface FilterConfigUpdate {
  target_locations?: string[]
  backend_keywords?: string[]
  exclude_keywords?: string[]
  tech_stack_keywords?: string[]
  min_experience?: number
  max_experience?: number
  llm_suggestion_threshold?: number
}

export interface ScrapeRun {
  id: number
  started_at: string
  completed_at?: string | null
  duration_sec: number
  total_companies: number
  companies_with_jobs: number
  companies_zero_jobs: number
  total_raw_jobs: number
  total_valid_leads: number
  avg_match_score: number
  status: string
  error_log?: string | null
  created_at: string
}

export interface ScrapeRunListResponse {
  items: ScrapeRun[]
  total: number
  page: number
  page_size: number
}

export interface Export {
  id: number
  filename: string
  row_count: number
  avg_match_score: number
  download_url: string
  created_at: string
}

export interface ExportListResponse {
  items: Export[]
  total: number
}

export interface ExportRequest {
  min_score?: number
  date_from?: string
  date_to?: string
  company?: string
  limit?: number
}
