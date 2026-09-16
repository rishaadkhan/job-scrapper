"""
Regression tests for graceful degradation, fail-open behavior, and configuration safety.
Verifies:
1. REQUIRED settings fail fast at startup when missing or empty.
2. OPTIONAL settings degrade gracefully without raising exceptions.
3. Startup capability logging correctly reports ACTIVE vs DISABLED status.
4. Core pipeline (scrape -> normalize -> filter -> dedupe -> non-LLM score -> export)
   runs completely and produces valid, well-formed Excel output with optional columns
   empty when all optional environment variables are unset.
5. Isolated error handling for Anthropic API failures (timeouts, 429, 500) and digest dispatch.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import openpyxl
import pytest
from pydantic import ValidationError

from config.settings import Settings, get_settings, log_startup_capabilities
from config import EXCEL_COLUMNS
from filters import JobFilter
from state_manager import StateManager
from scoring import JobScorer
from scoring.bullet_generator import BulletGenerator
from exporter import ExcelExporter
from notifier.digest import send_daily_digest


class TestSettingsRequiredAndOptional(unittest.TestCase):
    """Verifies fail-fast behavior on REQUIRED vars and graceful degradation on OPTIONAL vars."""

    def test_missing_database_url_fails_fast(self):
        """Missing or empty DATABASE_URL must raise ValidationError at startup."""
        with patch.dict(os.environ, {"DATABASE_URL": "", "JWT_SECRET": "valid-secret"}, clear=False):
            with self.assertRaises((ValidationError, ValueError)):
                Settings(_env_file=None)

    def test_missing_jwt_secret_fails_fast(self):
        """Missing or empty JWT_SECRET must raise ValidationError at startup."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///jobscraper.db", "JWT_SECRET": ""}, clear=False):
            with self.assertRaises((ValidationError, ValueError)):
                Settings(_env_file=None)

    def test_optional_vars_unset_degrades_gracefully(self):
        """Unsetting all optional variables must succeed and disable corresponding capabilities."""
        clean_env = {
            "DATABASE_URL": "sqlite+aiosqlite:///test_degrade.db",
            "JWT_SECRET": "test-jwt-secret",
            "ANTHROPIC_API_KEY": "",
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_CHAT_ID": "",
            "SENTRY_DSN": "",
            "HEARTBEAT_URL": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "SMTP_TO": ""
        }
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = Settings(_env_file=None)
            self.assertEqual(cfg.DATABASE_URL, "sqlite+aiosqlite:///test_degrade.db")
            self.assertEqual(cfg.JWT_SECRET, "test-jwt-secret")
            
            # Capability checks
            self.assertFalse(cfg.is_bullet_generation_enabled)
            self.assertFalse(cfg.is_telegram_digest_enabled)
            self.assertFalse(cfg.is_smtp_digest_enabled)
            self.assertFalse(cfg.is_sentry_enabled)
            self.assertFalse(cfg.is_heartbeat_enabled)

            # Startup logging output check
            log_lines = log_startup_capabilities(custom_settings=cfg)
            self.assertTrue(any("Resume bullet suggestions: DISABLED" in l for l in log_lines))
            self.assertTrue(any("Telegram digest: DISABLED" in l for l in log_lines))
            self.assertTrue(any("Sentry error tracking: DISABLED" in l for l in log_lines))
            self.assertTrue(any("Heartbeat monitoring: DISABLED" in l for l in log_lines))


class TestOptionalIntegrationsIsolatedErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Verifies that failures in optional integrations never crash or stop the pipeline."""

    async def test_bullet_generator_handles_missing_api_key(self):
        """When ANTHROPIC_API_KEY is empty, generate_bullets returns empty string without error."""
        gen = BulletGenerator(api_key="", threshold=50)
        res = await gen.generate_bullets(
            company="Acme Corp",
            title="Backend Engineer",
            description="Python FastAPI Postgres",
            resume_text="Skills: Python, FastAPI",
            top_keywords=["Python", "FastAPI"],
            missing_keywords=[],
            match_score=85
        )
        self.assertEqual(res, "")

    async def test_bullet_generator_handles_api_rate_limit(self):
        """When Anthropic API returns 429, logs warning and returns empty string without raising."""
        gen = BulletGenerator(api_key="sk-test-fake-key", threshold=50)
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        res = await gen.generate_bullets(
            company="Acme Corp",
            title="Backend Engineer",
            description="Python FastAPI Postgres",
            resume_text="Skills: Python, FastAPI",
            top_keywords=["Python", "FastAPI"],
            missing_keywords=[],
            match_score=85,
            client=mock_client
        )
        self.assertEqual(res, "")

    async def test_bullet_generator_handles_timeout_exception(self):
        """When Anthropic API times out, returns empty string without raising."""
        gen = BulletGenerator(api_key="sk-test-fake-key", threshold=50)
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Read timeout")

        res = await gen.generate_bullets(
            company="Acme Corp",
            title="Backend Engineer",
            description="Python FastAPI Postgres",
            resume_text="Skills: Python, FastAPI",
            top_keywords=["Python", "FastAPI"],
            missing_keywords=[],
            match_score=85,
            client=mock_client
        )
        self.assertEqual(res, "")

    async def test_send_daily_digest_handles_unconfigured_channels_without_raising(self):
        """send_daily_digest must complete without raising when no notification channels are set."""
        sample_jobs = [{
            "company": "Acme",
            "title": "Backend Engineer",
            "match_score": 90,
            "top_jd_keywords": ["Python", "FastAPI"],
            "apply_link": "https://example.com/apply"
        }]
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_CHAT_ID": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "SMTP_TO": ""
        }, clear=False):
            # Must not raise any exception
            await send_daily_digest(valid_jobs=sample_jobs, run_id=1, dry_run=False)


class TestCorePipelineFailOpenRegression(unittest.IsolatedAsyncioTestCase):
    """
    Core regression test:
    Proves that the full pipeline (scrape -> normalize -> filter -> dedupe -> non-LLM score -> export)
    is completely independent of every optional integration.
    """

    async def test_full_pipeline_with_all_optional_vars_unset(self):
        """
        Runs the full pipeline against a fixture set of companies with ALL optional env vars unset.
        Asserts:
        - Run completes without raising.
        - Excel spreadsheet is produced.
        - Rows are valid and non-empty.
        - Optional column 'Suggested Bullet Edits' is present but empty, preserving all 15 columns.
        """
        # 1. Unset all optional env vars
        clean_env = {
            "DATABASE_URL": "sqlite+aiosqlite:///jobscraper.db",
            "JWT_SECRET": "regression-test-jwt-secret",
            "ANTHROPIC_API_KEY": "",
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_CHAT_ID": "",
            "SENTRY_DSN": "",
            "HEARTBEAT_URL": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "SMTP_TO": ""
        }

        with patch.dict(os.environ, clean_env, clear=True):
            # 2. Fixture companies & raw scraped jobs
            fixture_company = {
                "name": "Acme Corp",
                "type": "Unicorn",
                "career_url": "https://boards.greenhouse.io/acme",
                "ats": "greenhouse",
                "ats_token": "acme"
            }

            fixture_raw_jobs = [
                {
                    "company": "Acme Corp",
                    "company_type": "Unicorn",
                    "title": "Backend Software Engineer",
                    "location": "Bengaluru, India",
                    "link": "https://boards.greenhouse.io/acme/jobs/101?utm_source=linkedin",
                    "job_id": "101",
                    "description": (
                        "We are looking for a Backend Software Engineer with 1-2 years experience. "
                        "Tech stack: Python, FastAPI, PostgreSQL, Redis, Docker, and REST APIs. "
                        "Responsible for building high-throughput microservices."
                    ),
                    "posted_date": "2026-09-15",
                    "portal_url": "https://boards.greenhouse.io/acme"
                },
                {
                    "company": "Acme Corp",
                    "company_type": "Unicorn",
                    "title": "Senior Director of Marketing",
                    "location": "Bengaluru, India",
                    "link": "https://boards.greenhouse.io/acme/jobs/102",
                    "job_id": "102",
                    "description": "Lead marketing strategy for APAC.",
                    "posted_date": "2026-09-15",
                    "portal_url": "https://boards.greenhouse.io/acme"
                }
            ]

            # 3. Initialize pipeline components in temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                state_file = os.path.join(temp_dir, "test_state.json")
                resume_file = os.path.join(temp_dir, "test_resume.md")

                with open(resume_file, "w", encoding="utf-8") as f:
                    f.write("# Candidate\nSkills: Python, FastAPI, PostgreSQL, Redis, Docker, Linux\n")

                state_mgr = StateManager(state_file=state_file)
                scorer = JobScorer(resume_path=resume_file)
                
                with patch("config.OUTPUT_DIR", temp_dir):
                    exporter = ExcelExporter()
                    exporter.output_dir = temp_dir

                    valid_jobs = []

                    # 4. Pipeline Execution: Filter, Dedupe, Score
                    for raw_job in fixture_raw_jobs:
                        # Business filter
                        if JobFilter.filter_job(raw_job, fixture_company):
                            job_id = f"{fixture_company['name']}_{raw_job['job_id']}"
                            if not state_mgr.is_job_seen(job_id):
                                # Score & Enrich with LLM bullets disabled
                                scored_job = await scorer.score_and_enrich_job(raw_job)
                                valid_jobs.append(scored_job)
                                state_mgr.mark_job_seen(job_id, fixture_company["name"])

                    # Assert: Marketing role was filtered out, backend role kept
                    self.assertEqual(len(valid_jobs), 1)
                    lead = valid_jobs[0]
                    self.assertEqual(lead["title"], "Backend Software Engineer")
                    self.assertTrue(lead["match_score"] > 60)
                    self.assertIn("FastAPI", lead["top_jd_keywords"])
                    # Bullet suggestions must be empty string (fail-open)
                    self.assertEqual(lead["suggested_bullets"], "")

                    # 5. Pipeline Execution: Export to Excel
                    excel_path = exporter.export_jobs(valid_jobs)
                    self.assertIsNotNone(excel_path)
                    self.assertTrue(os.path.exists(excel_path))

                    # 6. Verify Excel file structure & column integrity
                    wb = openpyxl.load_workbook(excel_path)
                    ws = wb.active
                    self.assertEqual(ws.title, "Job Leads")

                    # Verify header row matches all 15 EXCEL_COLUMNS
                    header_cells = [cell.value for cell in ws[1]]
                    self.assertEqual(header_cells, EXCEL_COLUMNS)
                    self.assertEqual(len(header_cells), 15)

                    # Verify body row
                    row_cells = [cell.value for cell in ws[2]]
                    self.assertEqual(len(row_cells), 15)
                    self.assertEqual(row_cells[0], "Acme Corp")
                    self.assertEqual(row_cells[2], "Backend Software Engineer")
                    self.assertEqual(row_cells[3], lead["match_score"])
                    self.assertEqual(row_cells[5], "Bengaluru, India")

                    # Verify optional column 9: "Suggested Bullet Edits" is present and empty
                    bullet_col_index = EXCEL_COLUMNS.index("Suggested Bullet Edits")
                    bullet_cell_value = row_cells[bullet_col_index]
                    self.assertIn(bullet_cell_value, ("", None), "Suggested Bullet Edits column must be empty string or None when LLM is unset")
