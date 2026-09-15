"""Scraping utilities, per-domain rate limiting, and exponential backoff retry"""
import asyncio
import time
import re
import hashlib
from urllib.parse import urlparse, urlunparse
from typing import Dict, Optional, Tuple, Any, List
import httpx
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, RATE_LIMIT_DELAY, USER_AGENT


def clean_job_url(url: str) -> str:
    """Strips query parameters and fragments from a job URL for stable deduplication."""
    if not url:
        return ""
    parsed = urlparse(url)
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', '', ''))
    return clean


def derive_job_id(company: str, title: str, link: str = "", description: str = "", raw_id: str = "") -> str:
    """
    Derives a stable job_id:
    - Strips query params from tracked URLs.
    - Extracts ATS IDs where available.
    - Uses SHA-256 fallback hash of (company + normalized title + first 500 chars of JD)
      when no clean ID exists.
    """
    if raw_id and not raw_id.startswith('http') and len(raw_id) < 100:
        clean_raw = raw_id.split('?')[0].split('#')[0].strip()
        if clean_raw:
            return clean_raw

    if link:
        clean_url = clean_job_url(link)

        li_match = re.search(r'/jobs/view/(?:[a-zA-Z0-9-]+-)?(\d+)', clean_url)
        if li_match:
            return f"li_{li_match.group(1)}"

        gh_match = re.search(r'/jobs?/(\d+)/?$', clean_url)
        if gh_match:
            return gh_match.group(1)

        path_parts = [p for p in urlparse(clean_url).path.split('/') if p]
        if path_parts and path_parts[-1] not in ['jobs', 'careers', 'search', 'results', 'en', 'en-in', 'us']:
            return path_parts[-1]

    norm_company = company.strip().lower() if company else ""
    norm_title = re.sub(r'\s+', ' ', title.strip().lower()) if title else ""
    norm_jd = re.sub(r'\s+', ' ', description[:500].strip().lower()) if description else ""

    hash_input = f"{norm_company}:{norm_title}:{norm_jd}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]


def validate_job_page(description: str) -> Tuple[bool, str]:
    """
    Validates that a fetched page is not a dead link or SPA shell.
    Returns (is_valid: bool, rejection_reason: str).
    """
    if not description or not description.strip():
        return False, "Empty job description"

    desc_strip = description.strip()
    if len(desc_strip) < 50:
        return False, f"Description too short ({len(desc_strip)} chars)"

    desc_lower = desc_strip.lower()
    if "page not found" in desc_lower or "404 not found" in desc_lower:
        return False, "Dead link / 404 ('Page not found')"

    if "enable javascript" in desc_lower or "javascript is disabled" in desc_lower:
        return False, "SPA shell detected ('enable JavaScript')"

    return True, ""


class DomainRateLimiter:
    """Per-domain rate limiter ensuring polite crawl intervals across external hosts."""

    def __init__(self, default_delay: float = 0.5):
        self.default_delay = default_delay
        self._locks: Dict[str, asyncio.Lock] = {}
        self._last_request_time: Dict[str, float] = {}

    def _get_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc.lower() or "default"
        except Exception:
            return "default"

    async def throttle(self, url: str):
        domain = self._get_domain(url)
        if domain not in self._locks:
            self._locks[domain] = asyncio.Lock()

        async with self._locks[domain]:
            now = time.monotonic()
            elapsed = now - self._last_request_time.get(domain, 0.0)
            if elapsed < self.default_delay:
                await asyncio.sleep(self.default_delay - elapsed)
            self._last_request_time[domain] = time.monotonic()


async def async_fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    rate_limiter: Optional[DomainRateLimiter] = None,
    **kwargs
) -> Optional[httpx.Response]:
    """
    Executes an HTTP request with per-domain rate limiting and exponential backoff
    on transient network failures or HTTP 429/5xx responses.
    """
    for attempt in range(max_retries + 1):
        if rate_limiter:
            await rate_limiter.throttle(url)
        try:
            if method.upper() == "POST":
                response = await client.post(url, **kwargs)
            else:
                response = await client.get(url, **kwargs)

            if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
                else:
                    delay = backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
                continue

            return response
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError):
            if attempt < max_retries:
                delay = backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            return None
        except Exception:
            return None
    return None


class JobScraper:
    """Backward-compatible synchronous scraper class."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

    def scrape_company(self, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        career_url = company.get('career_url', '')
        if not career_url or 'linkedin.com' in career_url.lower():
            return []

        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(career_url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return []
            return self._scrape_generic(response, company)
        except Exception:
            return []

    def _scrape_generic(self, response, company: Dict[str, Any]) -> List[Dict[str, Any]]:
        jobs = []
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

        for elem in job_elements[:50]:
            try:
                link_elem = elem.find('a') if elem.name != 'a' else elem
                if not link_elem:
                    continue

                location_elem = (
                    elem.find(class_=re.compile(r'location|city|place|region', re.I)) or
                    elem.find('span', class_=re.compile(r'loc', re.I))
                )
                location = location_elem.get_text(separator=' ', strip=True) if location_elem else ''

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

                job_keywords = ['engineer', 'developer', 'architect', 'analyst', 'designer', 'manager', 'lead', 'sde', 'specialist']
                if not any(re.search(rf'\b{re.escape(kw)}\b', title_lower) for kw in job_keywords):
                    continue

                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    base_url = '/'.join(company['career_url'].split('/')[:3])
                    link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"

                job_id = derive_job_id(company['name'], title, link=link)

                jobs.append({
                    'company': company['name'],
                    'company_type': company['type'],
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id,
                    'description': '',
                    'posted_date': '',
                    'portal_url': company['career_url']
                })
            except Exception:
                continue

        return jobs

    def fetch_job_description(self, job_url: str) -> str:
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(job_url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return ''

            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            desc_elem = (
                soup.find('div', class_=re.compile(r'description|content|details|posting-page', re.I)) or
                soup.find('div', id=re.compile(r'description|content|details', re.I)) or
                soup.find('section', class_=re.compile(r'description|content', re.I)) or
                soup.find('main')
            )

            text = desc_elem.get_text(separator=' ', strip=True) if desc_elem else soup.get_text(separator=' ', strip=True)
            return text[:5000].strip()
        except Exception:
            return ''
