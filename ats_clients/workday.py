"""Workday CXS JSON API Client (wday/cxs/{tenant}/{site}/jobs)"""
import asyncio
from typing import List, Dict, Any
import re
import httpx
from .base import BaseATSClient, clean_html_to_text


class WorkdayClient(BaseATSClient):
    """Client for Workday Candidate Experience Services (CXS) JSON endpoints."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        tenant = company.get('ats_token') or company.get('tenant')
        host = company.get('workday_host')
        site = company.get('workday_site')

        # Fallback to parsing from career_url if not explicitly provided
        if not (host and tenant and site):
            career_url = company.get('career_url', '')
            m = re.search(r'https?://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-zA-Z]{2}(?:-[a-zA-Z]{2,4})?/)?([^/?#]+)', career_url)
            if m:
                url_tenant = m.group(1)
                # Override erroneous cluster tokens like 'wd5' with actual subdomain tenant
                if not tenant or re.match(r'^wd\d+$', str(tenant)):
                    tenant = url_tenant
                else:
                    tenant = tenant or url_tenant
                host = host or f"{url_tenant}.{m.group(2)}.myworkdayjobs.com"
                site = site or m.group(3)

        if not (host and tenant and site):
            return []

        jobs_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        jobs: List[Dict[str, Any]] = []

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # Query for India jobs with limit=20 (Workday CXS hard-rejects limit > 20 with HTTP 400)
        payload = {
            'appliedFacets': {},
            'limit': 20,
            'offset': 0,
            'searchText': 'India'
        }

        try:
            response = await client.post(jobs_url, json=payload, headers=headers, timeout=15.0)
            if response.status_code != 200:
                # Retry with empty search text if India search returned nothing or error
                payload['searchText'] = ''
                payload['limit'] = 20
                response = await client.post(jobs_url, json=payload, headers=headers, timeout=15.0)
                if response.status_code != 200:
                    return []

            data = response.json()
            postings = data.get('jobPostings', [])
            valid_postings = [p for p in postings if (p.get('title') or '').strip()]

            async def _fetch_detail(raw: Dict[str, Any]) -> Dict[str, Any]:
                title = (raw.get('title') or '').strip()
                location = raw.get('locationsText', '') or ''
                external_path = raw.get('externalPath', '')
                bullet_fields = raw.get('bulletFields', [])
                req_id = bullet_fields[0] if bullet_fields else ''

                link = f"https://{host}/en-US/{site}{external_path}" if external_path else company.get('career_url', '')
                job_id = req_id or (external_path.split('_')[-1] if '_' in external_path else external_path) or title
                posted_date = raw.get('postedOn', '') or ''
                description = ""

                if external_path:
                    try:
                        detail_url = f"https://{host}/wday/cxs/{tenant}/{site}{external_path}"
                        detail_resp = await client.get(detail_url, headers=headers, timeout=10.0)
                        if detail_resp.status_code == 200:
                            detail_info = detail_resp.json().get('jobPostingInfo', {})
                            desc_html = detail_info.get('jobDescription', '')
                            description = clean_html_to_text(desc_html)
                            if not location and detail_info.get('location'):
                                location = str(detail_info.get('location'))
                    except Exception:
                        description = ""

                return {
                    'company': company['name'],
                    'company_type': company.get('type', 'Tier-1 GCC'),
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id,
                    'description': description,
                    'posted_date': posted_date,
                    'portal_url': company.get('career_url', jobs_url)
                }

            detail_tasks = [_fetch_detail(p) for p in valid_postings]
            jobs = await asyncio.gather(*detail_tasks)
            return list(jobs)

        except Exception:
            return []

