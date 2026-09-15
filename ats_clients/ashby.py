"""Ashby JSON API Client (api.ashbyhq.com)"""
from typing import List, Dict, Any
import httpx
from .base import BaseATSClient, clean_html_to_text


class AshbyClient(BaseATSClient):
    """Client for Ashby public job-board JSON API."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        token = company.get('ats_token') or company.get('ats_id')
        if not token:
            return []

        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        jobs: List[Dict[str, Any]] = []

        try:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                return []

            data = response.json()
            raw_jobs = data.get('jobs', [])

            for raw in raw_jobs:
                title = (raw.get('title') or '').strip()
                if not title:
                    continue

                location = raw.get('location', '') or ''
                secondary_locs = raw.get('secondaryLocations', [])
                if secondary_locs and isinstance(secondary_locs, list):
                    extra_locs = [s.get('location', '') for s in secondary_locs if isinstance(s, dict) and s.get('location')]
                    if extra_locs:
                        location = f"{location}, {', '.join(extra_locs)}" if location else ', '.join(extra_locs)

                link = raw.get('jobUrl') or raw.get('applyUrl') or ''
                job_id = str(raw.get('id') or '')

                desc_plain = raw.get('descriptionPlain', '')
                if desc_plain:
                    description = desc_plain[:5000].strip()
                else:
                    description = clean_html_to_text(raw.get('descriptionHtml', ''))

                published_at = raw.get('publishedAt', '') or ''

                jobs.append({
                    'company': company['name'],
                    'company_type': company.get('type', 'Tier-1 GCC'),
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id or link,
                    'description': description,
                    'posted_date': published_at,
                    'portal_url': company.get('career_url', url)
                })

        except Exception:
            pass

        return jobs
