"""
Unit tests for Company Ingestion Engine, Deduplication, and ATS Auto-Detection.
Verifies:
- Normalization (stripping suffixes: 'India', 'Pvt Ltd', 'Inc', 'Technologies', etc.)
- Exact and near-duplicate deduplication
- Proving near-duplicates ('Zoom' vs 'Zoom India') are flagged and NOT silently added
- ATS pattern detection and active endpoint probing
- Honest fallback to 'unknown' ATS rather than guessing
- CLI input file parsing across formats
"""
import unittest
from unittest.mock import patch, MagicMock

from expand_companies import (
    normalize_company_name,
    fuzzy_match_company,
    detect_ats,
    probe_ats,
    detect_or_probe_company_ats,
    DEFAULT_LOCATIONS
)
from manage import parse_input_file
import tempfile
import os


class TestCompanyNormalizationAndDedup(unittest.TestCase):
    """Test suite for name normalization and fuzzy deduplication."""

    def test_normalize_strips_geographic_suffixes(self):
        self.assertEqual(normalize_company_name("Zoom India"), "zoom")
        self.assertEqual(normalize_company_name("Shopify APAC"), "shopify")
        self.assertEqual(normalize_company_name("Stripe US"), "stripe")
        self.assertEqual(normalize_company_name("GitLab Global"), "gitlab")

    def test_normalize_strips_corporate_suffixes(self):
        self.assertEqual(normalize_company_name("Zoom India Pvt Ltd"), "zoom")
        self.assertEqual(normalize_company_name("Chargebee Technologies"), "chargebee")
        self.assertEqual(normalize_company_name("Nutanix Inc."), "nutanix")
        self.assertEqual(normalize_company_name("Uber Technologies, Inc."), "uber")
        self.assertEqual(normalize_company_name("Databricks India Private Limited"), "databricks")
        self.assertEqual(normalize_company_name("Acme Software Solutions LLC"), "acme")

    def test_normalize_bracketed_text_and_punctuation(self):
        self.assertEqual(normalize_company_name("Zoom (India)"), "zoom")
        self.assertEqual(normalize_company_name("Swiggy (India Pvt Ltd)"), "swiggy")
        self.assertEqual(normalize_company_name("Cisco Systems - India"), "cisco")

    def test_near_duplicate_zoom_flagged_not_added(self):
        """
        Critical test: Verifies that 'Zoom' is flagged as a near-duplicate
        when 'Zoom India' exists, and is NOT silently passed or merged.
        """
        existing_companies = [
            {"id": 1, "name": "Zoom India", "career_url": "https://careers.zoom.us", "ats": "html_fallback"}
        ]
        match = fuzzy_match_company("Zoom", existing_companies)
        self.assertIsNotNone(match)
        self.assertTrue(match["matched"])
        self.assertEqual(match["existing_company"]["name"], "Zoom India")
        self.assertEqual(match["match_type"], "Normalized Base Match")
        self.assertGreaterEqual(match["similarity"], 0.95)

    def test_near_duplicate_chargebee_technologies_flagged(self):
        existing_companies = [
            {"id": 2, "name": "Chargebee", "career_url": "https://chargebee.com/careers", "ats": "html_fallback"}
        ]
        match = fuzzy_match_company("Chargebee Technologies Pvt Ltd", existing_companies)
        self.assertIsNotNone(match)
        self.assertEqual(match["existing_company"]["name"], "Chargebee")
        self.assertEqual(match["match_type"], "Normalized Base Match")

    def test_non_duplicate_passes_cleanly(self):
        existing_companies = [
            {"id": 1, "name": "Zoom India", "career_url": "https://careers.zoom.us"},
            {"id": 2, "name": "Chargebee", "career_url": "https://chargebee.com"}
        ]
        match = fuzzy_match_company("Supabase", existing_companies)
        self.assertIsNone(match)


class TestATSAutoDetection(unittest.TestCase):
    """Test suite for URL pattern detection and probing."""

    def test_detect_ats_greenhouse_urls(self):
        ats, token, _ = detect_ats("https://boards.greenhouse.io/databricks")
        self.assertEqual(ats, "greenhouse")
        self.assertEqual(token, "databricks")

        ats2, token2, _ = detect_ats("https://job-boards.greenhouse.io/stripe/jobs/12345")
        self.assertEqual(ats2, "greenhouse")
        self.assertEqual(token2, "stripe")

    def test_detect_ats_lever_urls(self):
        ats, token, _ = detect_ats("https://jobs.lever.co/notion")
        self.assertEqual(ats, "lever")
        self.assertEqual(token, "notion")

    def test_detect_ats_ashby_urls(self):
        ats, token, _ = detect_ats("https://jobs.ashbyhq.com/ramp")
        self.assertEqual(ats, "ashby")
        self.assertEqual(token, "ramp")

    def test_detect_ats_smartrecruiters_urls(self):
        ats, token, _ = detect_ats("https://careers.smartrecruiters.com/uber")
        self.assertEqual(ats, "smartrecruiters")
        self.assertEqual(token, "uber")

    def test_detect_ats_workday_urls(self):
        ats, tenant, site = detect_ats("https://snowflake.wd1.myworkdayjobs.com/Snowflake_Careers")
        self.assertEqual(ats, "workday")
        self.assertEqual(tenant, "snowflake")
        self.assertEqual(site, "Snowflake_Careers")

    @patch("requests.Session.get")
    def test_probe_ats_greenhouse_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobs": [{"id": 101, "title": "Backend Engineer"}]}
        mock_get.return_value = mock_resp

        result = probe_ats("Monzo")
        self.assertTrue(result["resolved"])
        self.assertEqual(result["ats"], "greenhouse")
        self.assertEqual(result["token"], "monzo")

    @patch("requests.Session.get")
    def test_probe_ats_unresolved_marked_unknown(self, mock_get):
        """
        Critical test: If no known ATS pattern or probe resolves,
        ats must be marked 'unknown' rather than guessing a token.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = probe_ats("CompletelyUnknownEnterprise1234")
        self.assertFalse(result["resolved"])
        self.assertEqual(result["ats"], "unknown")
        self.assertIsNone(result["token"])


class TestInputParser(unittest.TestCase):
    """Test suite for CLI input file parsing."""

    def test_parse_plain_text_with_category_headers(self):
        content = """
# Tier-1 GCC
Zoom
Datadog

# Unicorn
Ramp
Linear

# High-Paying Startup
Supabase
        """.strip()

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(content)
            tf_path = tf.name

        try:
            candidates = parse_input_file(tf_path)
            self.assertEqual(len(candidates), 5)
            self.assertEqual(candidates[0]["name"], "Zoom")
            self.assertEqual(candidates[0]["type"], "Tier-1 GCC")
            self.assertEqual(candidates[2]["name"], "Ramp")
            self.assertEqual(candidates[2]["type"], "Unicorn")
            self.assertEqual(candidates[4]["name"], "Supabase")
            self.assertEqual(candidates[4]["type"], "High-Paying Startup")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_parse_csv_file(self):
        content = """name,type,career_url
Acme Corp,MNC,https://acme.com/jobs
Beta Labs,Startup,https://jobs.ashbyhq.com/beta
"""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tf:
            tf.write(content)
            tf_path = tf.name

        try:
            candidates = parse_input_file(tf_path)
            self.assertEqual(len(candidates), 2)
            self.assertEqual(candidates[0]["name"], "Acme Corp")
            self.assertEqual(candidates[0]["type"], "MNC")
            self.assertEqual(candidates[1]["name"], "Beta Labs")
            self.assertEqual(candidates[1]["career_url"], "https://jobs.ashbyhq.com/beta")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


if __name__ == "__main__":
    unittest.main()
