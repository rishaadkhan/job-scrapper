"""Async HTML Fallback Client for companies without public JSON endpoints"""
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
import httpx
from .base import BaseATSClient, clean_html_to_text
from scraper import derive_job_id


class HTMLFallbackClient(BaseATSClient):
    """HTML scraping fallback for companies without dedicated ATS JSON APIs."""

    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        career_url = company.get('career_url', '')
        if not career_url:
            return []

        # Explicitly reject and skip LinkedIn scraping per ToS compliance (Blueprint §1.6 / §5)
        if 'linkedin.com' in career_url.lower():
            return []

        jobs: List[Dict[str, Any]] = []

        try:
            response = await client.get(career_url, timeout=15.0, follow_redirects=True)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            job_elements = (
                soup.find_all('div', class_=re.compile(r'job|position|opening|career', re.I)) +
                soup.find_all('li', class_=re.compile(r'job|position|opening', re.I)) +
                soup.find_all('a', href=re.compile(r'job|career|position', re.I))
            )

            exclude_titles = [
                'cookie', 'privacy', 'policy', 'preferences', 'filter', 'clear',
                'talent community', 'join', 'sign in', 'login', 'register',
                'search', 'apply', 'view', 'home', 'about', 'contact'
            ]

            job_keywords = ['engineer', 'developer', 'architect', 'analyst', 'designer', 'manager', 'lead', 'sde', 'specialist']

            seen_links = set()

            for elem in job_elements[:40]:
                try:
                    link_elem = elem.find('a') if elem.name != 'a' else elem
                    if not link_elem:
                        continue

                    # Dedicated location element
                    loc_elem = (
                        elem.find(class_=re.compile(r'location|city|place|region', re.I)) or
                        elem.find('span', class_=re.compile(r'loc', re.I))
                    )
                    location = loc_elem.get_text(separator=' ', strip=True) if loc_elem else ''

                    # Dedicated title element
                    title_elem = (
                        elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or
                        elem.find(class_=re.compile(r'title|role|position|name', re.I)) or
                        link_elem
                    )
                    title = title_elem.get_text(separator=' ', strip=True)

                    if location and location in title:
                        title = title.replace(location, '').strip()

                    title = re.sub(r'\s+', ' ', title).strip()

                    if len(title) < 5 or len(title) > 120:
                        continue

                    title_lower = title.lower()
                    if any(word in title_lower for word in exclude_titles):
                        continue

                    if not any(re.search(rf'\b{re.escape(kw)}\b', title_lower) for kw in job_keywords):
                        continue

                    link = link_elem.get('href', '')
                    if not link or link in seen_links:
                        continue

                    if not link.startswith('http'):
                        base_parts = career_url.split('/')[:3]
                        base_url = '/'.join(base_parts)
                        link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"

                    seen_links.add(link)
                    job_id = derive_job_id(company['name'], title, link=link)

                    # Fetch description asynchronously
                    description = ""
                    try:
                        desc_resp = await client.get(link, timeout=10.0, follow_redirects=True)
                        if desc_resp.status_code == 200:
                            description = clean_html_to_text(desc_resp.text)
                    except Exception:
                        description = ""

                    jobs.append({
                        'company': company['name'],
                        'company_type': company.get('type', 'Tier-1 GCC'),
                        'title': title,
                        'location': location,
                        'link': link,
                        'job_id': job_id,
                        'description': description,
                        'posted_date': '',
                        'portal_url': career_url
                    })
                except Exception:
                    continue

        except Exception:
            pass

        return jobs
