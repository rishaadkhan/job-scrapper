"""Lever JSON API Client (api.lever.co)"""
from typing import List, Dict, Any
from datetime import datetime, timezone
import httpx
from .base import BaseATSClient, clean_html_to_text


class LeverClient(BaseATSClient):
    """Client for Lever public postings JSON API."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        token = company.get('ats_token') or company.get('ats_id')
        if not token:
            return []

        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        jobs: List[Dict[str, Any]] = []

        try:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                return []

            raw_postings = response.json()
            if not isinstance(raw_postings, list):
                return []

            for raw in raw_postings:
                title = (raw.get('text') or '').strip()
                if not title:
                    continue

                categories = raw.get('categories') or {}
                location = categories.get('location', '') or ''
                all_locations = categories.get('allLocations', [])
                if not location and all_locations:
                    location = ', '.join(all_locations)

                link = raw.get('hostedUrl') or raw.get('applyUrl') or ''
                job_id = str(raw.get('id') or '')

                desc_plain = raw.get('descriptionPlain', '')
                if desc_plain:
                    description = desc_plain[:5000].strip()
                else:
                    description = clean_html_to_text(raw.get('description', ''))

                created_at_ms = raw.get('createdAt')
                posted_date = ''
                if created_at_ms and isinstance(created_at_ms, (int, float)):
                    try:
                        posted_date = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc).strftime('%Y-%m-%d')
                    except Exception:
                        posted_date = ''

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

        except Exception:
            pass

        return jobs
