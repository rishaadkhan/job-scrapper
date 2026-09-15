"""Greenhouse JSON API Client (boards-api.greenhouse.io)"""
from typing import List, Dict, Any
import httpx
from .base import BaseATSClient, clean_html_to_text


class GreenhouseClient(BaseATSClient):
    """Client for Greenhouse public boards JSON API."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        token = company.get('ats_token') or company.get('ats_id')
        if not token:
            return []

        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
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

                loc_data = raw.get('location')
                if isinstance(loc_data, dict):
                    location = loc_data.get('name', '') or ''
                else:
                    location = str(loc_data or '')

                link = raw.get('absolute_url', '')
                job_id = str(raw.get('id') or '')
                content_html = raw.get('content', '')
                description = clean_html_to_text(content_html)
                posted_date = raw.get('updated_at', '') or ''

                jobs.append({
                    'company': company['name'],
                    'company_type': company.get('type', 'Tier-1 GCC'),
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id or link,
                    'description': description,
                    'posted_date': posted_date,
                    'portal_url': company.get('career_url', url)
                })

        except Exception as e:
            # Fault isolation
            pass

        return jobs
