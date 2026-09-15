"""Unit and integration tests for ATS JSON API clients and async engine"""
import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from ats_clients import (
    get_ats_client,
    GreenhouseClient,
    LeverClient,
    AshbyClient,
    SmartRecruitersClient,
    WorkdayClient,
    HTMLFallbackClient,
    clean_html_to_text
)
from scraper import DomainRateLimiter, async_fetch_with_retry


class TestATSClientDispatcher(unittest.TestCase):
    """Tests for ATS client dispatcher and factory."""

    def test_dispatcher_routing(self):
        self.assertIsInstance(get_ats_client('greenhouse'), GreenhouseClient)
        self.assertIsInstance(get_ats_client('lever'), LeverClient)
        self.assertIsInstance(get_ats_client('ashby'), AshbyClient)
        self.assertIsInstance(get_ats_client('smartrecruiters'), SmartRecruitersClient)
        self.assertIsInstance(get_ats_client('workday'), WorkdayClient)
        self.assertIsInstance(get_ats_client('html_fallback'), HTMLFallbackClient)
        self.assertIsInstance(get_ats_client('unknown_ats'), HTMLFallbackClient)


class TestGreenhouseClient(unittest.IsolatedAsyncioTestCase):
    """Tests for Greenhouse JSON API client."""

    async def test_greenhouse_fetch_jobs_parsing(self):
        client = GreenhouseClient()
        mock_company = {
            'name': 'Stripe',
            'type': 'Tier-1 GCC',
            'ats': 'greenhouse',
            'ats_token': 'stripe',
            'career_url': 'https://stripe.com/jobs'
        }

        mock_payload = {
            'jobs': [
                {
                    'id': 123456,
                    'title': 'Backend Software Engineer',
                    'location': {'name': 'Bengaluru, India'},
                    'absolute_url': 'https://boards.greenhouse.io/stripe/jobs/123456',
                    'content': '<p>Join our <b>core payments</b> team.</p>',
                    'updated_at': '2026-09-12T00:00:00Z'
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_http_client.get.return_value = mock_resp

        jobs = await client.fetch_jobs(mock_company, mock_http_client)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job['title'], 'Backend Software Engineer')
        self.assertEqual(job['location'], 'Bengaluru, India')
        self.assertEqual(job['job_id'], '123456')
        self.assertIn('Join our core payments team.', job['description'])


class TestLeverClient(unittest.IsolatedAsyncioTestCase):
    """Tests for Lever JSON API client."""

    async def test_lever_fetch_jobs_parsing(self):
        client = LeverClient()
        mock_company = {
            'name': 'Affirm',
            'type': 'High-Paying Startup',
            'ats': 'lever',
            'ats_token': 'affirm',
            'career_url': 'https://jobs.lever.co/affirm'
        }

        mock_payload = [
            {
                'id': 'abc-123-uuid',
                'text': 'Software Development Engineer - Backend',
                'descriptionPlain': 'We are looking for a backend engineer.',
                'categories': {
                    'location': 'Bangalore',
                    'team': 'Engineering',
                    'allLocations': ['Bangalore', 'Remote']
                },
                'hostedUrl': 'https://jobs.lever.co/affirm/abc-123-uuid',
                'createdAt': 1726000000000
            }
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_http_client.get.return_value = mock_resp

        jobs = await client.fetch_jobs(mock_company, mock_http_client)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job['title'], 'Software Development Engineer - Backend')
        self.assertEqual(job['location'], 'Bangalore')
        self.assertEqual(job['job_id'], 'abc-123-uuid')
        self.assertEqual(job['description'], 'We are looking for a backend engineer.')


class TestAshbyClient(unittest.IsolatedAsyncioTestCase):
    """Tests for Ashby JSON API client."""

    async def test_ashby_fetch_jobs_parsing(self):
        client = AshbyClient()
        mock_company = {
            'name': 'Paddle',
            'type': 'High-Paying Startup',
            'ats': 'ashby',
            'ats_token': 'paddle',
            'career_url': 'https://jobs.ashbyhq.com/paddle'
        }

        mock_payload = {
            'jobs': [
                {
                    'id': 'ashby-uuid-999',
                    'title': 'Senior Platform Engineer',
                    'location': 'Bengaluru, India',
                    'secondaryLocations': [{'location': 'Remote'}],
                    'descriptionPlain': 'Build scalable distributed infrastructure.',
                    'jobUrl': 'https://jobs.ashbyhq.com/paddle/ashby-uuid-999',
                    'publishedAt': '2026-09-10'
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_http_client.get.return_value = mock_resp

        jobs = await client.fetch_jobs(mock_company, mock_http_client)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job['title'], 'Senior Platform Engineer')
        self.assertIn('Bengaluru', job['location'])
        self.assertEqual(job['job_id'], 'ashby-uuid-999')
        self.assertEqual(job['description'], 'Build scalable distributed infrastructure.')


class TestWorkdayClient(unittest.IsolatedAsyncioTestCase):
    """Tests for Workday CXS JSON API client."""

    async def test_workday_fetch_jobs_and_detail(self):
        client = WorkdayClient()
        mock_company = {
            'name': 'NVIDIA',
            'type': 'Tier-1 GCC',
            'ats': 'workday',
            'ats_token': 'nvidia',
            'workday_host': 'nvidia.wd5.myworkdayjobs.com',
            'workday_site': 'NVIDIAExternalCareerSite'
        }

        list_payload = {
            'total': 1,
            'jobPostings': [
                {
                    'title': 'Software Engineer - Autonomous Vehicles',
                    'externalPath': '/job/India-Pune/Software-Engineer_JR1001',
                    'locationsText': 'India, Pune',
                    'postedOn': 'Posted 2 Days Ago',
                    'bulletFields': ['JR1001']
                }
            ]
        }

        detail_payload = {
            'jobPostingInfo': {
                'title': 'Software Engineer - Autonomous Vehicles',
                'location': 'India, Pune',
                'jobDescription': '<p>Develop high-performance algorithms for perception and mapping.</p>'
            }
        }

        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = list_payload

        mock_detail_resp = MagicMock()
        mock_detail_resp.status_code = 200
        mock_detail_resp.json.return_value = detail_payload

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_http_client.post.return_value = mock_list_resp
        mock_http_client.get.return_value = mock_detail_resp

        jobs = await client.fetch_jobs(mock_company, mock_http_client)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job['title'], 'Software Engineer - Autonomous Vehicles')
        self.assertEqual(job['location'], 'India, Pune')
        self.assertEqual(job['job_id'], 'JR1001')
        self.assertIn('high-performance algorithms', job['description'])


class TestLinkedInRemovalAndHTMLFallback(unittest.IsolatedAsyncioTestCase):
    """Tests verifying LinkedIn scraping is explicitly rejected in HTMLFallbackClient."""

    async def test_linkedin_url_rejected_and_skipped(self):
        client = HTMLFallbackClient()
        mock_company = {
            'name': 'DeprecatedLinkedInCompany',
            'type': 'Unicorn',
            'ats': 'html_fallback',
            'career_url': 'https://in.linkedin.com/jobs/search?keywords=Chargebee'
        }

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        jobs = await client.fetch_jobs(mock_company, mock_http_client)

        # Must return empty list without making any network calls
        self.assertEqual(jobs, [])
        mock_http_client.get.assert_not_called()


class TestRateLimiterAndBackoff(unittest.IsolatedAsyncioTestCase):
    """Tests for per-domain rate limiting and exponential backoff retry."""

    async def test_rate_limiter_throttles_domain(self):
        limiter = DomainRateLimiter(default_delay=0.1)
        t0 = asyncio.get_event_loop().time()
        await limiter.throttle("https://api.example.com/endpoint1")
        await limiter.throttle("https://api.example.com/endpoint2")
        t1 = asyncio.get_event_loop().time()
        self.assertGreaterEqual(t1 - t0, 0.08)

    async def test_async_fetch_with_retry_on_429(self):
        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {}

        resp_200 = MagicMock()
        resp_200.status_code = 200

        mock_http_client.get.side_effect = [resp_429, resp_200]

        res = await async_fetch_with_retry(
            mock_http_client,
            "https://api.example.com/jobs",
            max_retries=2,
            backoff_factor=0.01
        )
        self.assertIsNotNone(res)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(mock_http_client.get.call_count, 2)


if __name__ == '__main__':
    unittest.main()
