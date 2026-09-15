"""ATS Client Module and Dispatcher"""
from typing import Dict, Any, List
import httpx
from .base import BaseATSClient, clean_html_to_text
from .greenhouse import GreenhouseClient
from .lever import LeverClient
from .ashby import AshbyClient
from .smartrecruiters import SmartRecruitersClient
from .workday import WorkdayClient
from .html_fallback import HTMLFallbackClient

_CLIENT_MAP: Dict[str, BaseATSClient] = {
    'greenhouse': GreenhouseClient(),
    'lever': LeverClient(),
    'ashby': AshbyClient(),
    'smartrecruiters': SmartRecruitersClient(),
    'workday': WorkdayClient(),
    'html_fallback': HTMLFallbackClient()
}


def get_ats_client(ats_name: str) -> BaseATSClient:
    """Returns the ATS client instance for the specified ATS type."""
    normalized = (ats_name or '').lower().strip()
    return _CLIENT_MAP.get(normalized, _CLIENT_MAP['html_fallback'])


async def fetch_company_jobs(company: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """
    Fetches job listings for a company by dispatching to its configured ATS client.
    Guarantees fault isolation so single company failures never crash the run.
    """
    ats_type = company.get('ats', 'html_fallback')
    handler = get_ats_client(ats_type)
    try:
        return await handler.fetch_jobs(company, client)
    except Exception:
        return []


__all__ = [
    'BaseATSClient',
    'GreenhouseClient',
    'LeverClient',
    'AshbyClient',
    'SmartRecruitersClient',
    'WorkdayClient',
    'HTMLFallbackClient',
    'get_ats_client',
    'fetch_company_jobs',
    'clean_html_to_text'
]
