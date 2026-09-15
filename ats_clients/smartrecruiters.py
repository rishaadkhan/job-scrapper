"""SmartRecruiters JSON API Client (api.smartrecruiters.com)"""
from typing import List, Dict, Any
import httpx
from .base import BaseATSClient, clean_html_to_text


class SmartRecruitersClient(BaseATSClient):
    """Client for SmartRecruiters public postings JSON API."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        token = company.get('ats_token') or company.get('ats_id')
        if not token:
            return []

        url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
        jobs: List[Dict[str, Any]] = []

        try:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                return []

            data = response.json()
            raw_postings = data.get('content', [])

            for raw in raw_postings:
                title = (raw.get('name') or '').strip()
                if not title:
                    continue

                loc_obj = raw.get('location') or {}
                city = loc_obj.get('city', '')
                region = loc_obj.get('region', '')
                country = loc_obj.get('country', '')
                loc_parts = [p for p in [city, region, country] if p]
                location = ', '.join(loc_parts)

                job_id = str(raw.get('id') or '')
                link = f"https://jobs.smartrecruiters.com/{token}/{job_id}"
                posted_date = raw.get('releasedDate', '') or ''

                # Fetch posting detail description if ID exists
                description = ""
                try:
                    detail_url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings/{job_id}"
                    detail_resp = await client.get(detail_url, timeout=10.0)
                    if detail_resp.status_code == 200:
                        detail_data = detail_resp.json()
                        sections = detail_data.get('jobAd', {}).get('sections', {})
                        sec_texts = []
                        for sec_key in ['jobDescription', 'qualifications', 'additionalInformation']:
                            sec_obj = sections.get(sec_key, {})
                            sec_text = sec_obj.get('text', '')
                            if sec_text:
                                sec_texts.append(clean_html_to_text(sec_text))
                        description = '\n\n'.join(sec_texts)[:5000].strip()
                except Exception:
                    description = ""

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
