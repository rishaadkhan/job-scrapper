"""Base class for ATS API clients and shared normalization helpers"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import httpx


def clean_html_to_text(html_content: str) -> str:
    """Converts HTML content to clean, readable plain text preserving block line breaks."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    for elem in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
        elem.decompose()

    for block in soup.find_all(['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr']):
        block.insert_after('\n')

    text = soup.get_text(separator=' ', strip=True)
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    text = '\n'.join([l for l in lines if l])
    return text[:5000].strip()


class BaseATSClient(ABC):
    """Abstract base class for all ATS API clients."""

    @abstractmethod
    async def fetch_jobs(self, company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """
        Fetches job postings from the ATS and returns a list of normalized job dicts:
        {
            'company': str,
            'company_type': str,
            'title': str,
            'location': str,
            'link': str,
            'job_id': str,
            'description': str,
            'posted_date': str,
            'portal_url': str
        }
        """
        pass
