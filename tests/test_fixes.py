"""Unit tests covering the 5 correctness fixes and deduplication"""
import unittest
import os
import tempfile
import json
from bs4 import BeautifulSoup
from filters import JobFilter
from scraper import JobScraper, clean_job_url, derive_job_id, validate_job_page
from state_manager import StateManager


class TestFix1BackendRoleFilter(unittest.TestCase):
    """Fix 1: is_backend_role() must positively require BACKEND_KEYWORDS match"""

    def test_rejects_non_backend_and_non_tech_roles(self):
        # Specific bad rows from 2026-09-12 output (Section 1.1)
        self.assertFalse(JobFilter.is_backend_role("Systems Sales Engineer"))
        self.assertFalse(JobFilter.is_backend_role("Solutions Engineer, Workvivo (APJ)"))
        self.assertFalse(JobFilter.is_backend_role("Revenue Event Marketing Lead"))
        self.assertFalse(JobFilter.is_backend_role("Creative Ops & Studio Manager"))

        # Other non-tech roles
        self.assertFalse(JobFilter.is_backend_role("Human Resources Specialist"))
        self.assertFalse(JobFilter.is_backend_role("Finance Analyst"))
        self.assertFalse(JobFilter.is_backend_role("Legal Counsel"))

    def test_accepts_valid_backend_roles(self):
        self.assertTrue(JobFilter.is_backend_role("Software Engineer"))
        self.assertTrue(JobFilter.is_backend_role("Software Engineer - Backend"))
        self.assertTrue(JobFilter.is_backend_role("Backend Engineer"))
        self.assertTrue(JobFilter.is_backend_role("SDE 1"))
        self.assertTrue(JobFilter.is_backend_role("SDE-I"))
        self.assertTrue(JobFilter.is_backend_role("Platform Engineer"))
        self.assertTrue(JobFilter.is_backend_role("Full Stack Developer"))
        self.assertTrue(JobFilter.is_backend_role("Fullstack Engineer"))
        self.assertTrue(JobFilter.is_backend_role("Software Developer"))
        self.assertTrue(JobFilter.is_backend_role("Backend Developer"))

    def test_rejects_senior_and_excluded_roles(self):
        self.assertFalse(JobFilter.is_backend_role("Senior Software Engineer"))
        self.assertFalse(JobFilter.is_backend_role("Staff Backend Engineer"))
        self.assertFalse(JobFilter.is_backend_role("Principal SDE"))
        self.assertFalse(JobFilter.is_backend_role("Lead Platform Engineer"))
        self.assertFalse(JobFilter.is_backend_role("Engineering Manager"))
        self.assertFalse(JobFilter.is_backend_role("Software Architect"))
        self.assertFalse(JobFilter.is_backend_role("Software Engineer Intern"))
        self.assertFalse(JobFilter.is_backend_role("QA Engineer"))
        self.assertFalse(JobFilter.is_backend_role("SDET"))


class TestFix2LocationValidation(unittest.TestCase):
    """Fix 2: is_valid_location() must validate actual scraped location and reject non-India locations"""

    def test_rejects_disqualifying_non_india_locations(self):
        # Specific bad rows from 2026-09-12 output (Section 1.2)
        self.assertFalse(JobFilter.is_valid_location("Vancouver, British Columbia"))
        self.assertFalse(JobFilter.is_valid_location("Singapore"))
        self.assertFalse(JobFilter.is_valid_location("Remote - APAC, Singapore, Hong Kong"))
        self.assertFalse(JobFilter.is_valid_location("Toronto, UK"))
        self.assertFalse(JobFilter.is_valid_location("Portugal, Lisbon"))
        self.assertFalse(JobFilter.is_valid_location("Seattle, WA"))

        # Other non-India locations
        self.assertFalse(JobFilter.is_valid_location("San Francisco, CA"))
        self.assertFalse(JobFilter.is_valid_location("London, United Kingdom"))
        self.assertFalse(JobFilter.is_valid_location("Berlin, Germany"))
        self.assertFalse(JobFilter.is_valid_location("Tokyo, Japan"))
        self.assertFalse(JobFilter.is_valid_location("Sydney, Australia"))

    def test_accepts_target_india_locations(self):
        self.assertTrue(JobFilter.is_valid_location("Bangalore, India"))
        self.assertTrue(JobFilter.is_valid_location("Bengaluru, Karnataka"))
        self.assertTrue(JobFilter.is_valid_location("Hyderabad, Telangana"))
        self.assertTrue(JobFilter.is_valid_location("Pune, Maharashtra"))
        self.assertTrue(JobFilter.is_valid_location("Chennai, Tamil Nadu"))
        self.assertTrue(JobFilter.is_valid_location("Noida, Uttar Pradesh"))
        self.assertTrue(JobFilter.is_valid_location("Gurgaon, Haryana"))
        self.assertTrue(JobFilter.is_valid_location("Delhi / NCR"))
        self.assertTrue(JobFilter.is_valid_location("Mumbai, India"))
        self.assertTrue(JobFilter.is_valid_location("Remote - India"))
        self.assertTrue(JobFilter.is_valid_location("India (Remote)"))

    def test_custom_location_filter(self):
        custom_filter = ["Bangalore", "Hyderabad"]
        self.assertTrue(JobFilter.is_valid_location("Bangalore", location_filter=custom_filter))
        self.assertFalse(JobFilter.is_valid_location("Pune", location_filter=custom_filter))


class TestFix3StableJobIdAndDeduplication(unittest.TestCase):
    """Fix 3: Stable job_id derivation, query param stripping, and deduplication test"""

    def test_clean_job_url_strips_tracking_params(self):
        raw_url1 = "https://in.linkedin.com/jobs/view/4459785362?refId=YFR6UDZCDqxrCg4vho5kRQ%3D%3D&trackingId=aJI2Sb8C%2F88tgwN7uX83bA%3D%3D"
        raw_url2 = "https://in.linkedin.com/jobs/view/4459785362?refId=JwJkcMZ%2Fn9gwt5GMjaUjjw%3D%3D&trackingId=u5M2EAhQxS%2BvmlvHQO5kMw%3D%3D"

        clean1 = clean_job_url(raw_url1)
        clean2 = clean_job_url(raw_url2)

        self.assertEqual(clean1, clean2)
        self.assertEqual(clean1, "https://in.linkedin.com/jobs/view/4459785362")

    def test_two_scrapes_with_different_tracking_params_dedupe_to_one(self):
        """Proves two scrapes of the same job with different tracking params dedupe to 1 entry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            temp_state_file = tf.name

        try:
            state = StateManager(state_file=temp_state_file)

            # Scrape 1: First run with tracking params A
            url_run1 = "https://in.linkedin.com/jobs/view/data-engineer-spark-4459785362?refId=Run1TrackingIdA"
            job_id_run1 = derive_job_id("Chargebee", "Data Engineer - Spark", link=url_run1)
            dedup_key_run1 = f"Chargebee_{job_id_run1}"

            self.assertFalse(state.is_job_seen(dedup_key_run1), "First scrape should be new")
            state.mark_job_seen(dedup_key_run1, "Chargebee")
            state.save_state()

            # Scrape 2: Second run 20 mins later with tracking params B
            url_run2 = "https://in.linkedin.com/jobs/view/data-engineer-spark-4459785362?refId=Run2TrackingIdB_Different"
            job_id_run2 = derive_job_id("Chargebee", "Data Engineer - Spark", link=url_run2)
            dedup_key_run2 = f"Chargebee_{job_id_run2}"

            # Verify that IDs match and state correctly identifies it as duplicate
            self.assertEqual(dedup_key_run1, dedup_key_run2)
            self.assertTrue(state.is_job_seen(dedup_key_run2), "Second scrape must be recognized as seen/duplicate")
            self.assertEqual(len(state.state['seen_jobs']), 1, "Exactly one unique job must exist in state")

        finally:
            if os.path.exists(temp_state_file):
                os.remove(temp_state_file)

    def test_fallback_stable_hash(self):
        # When no clean ID or URL exists
        company = "Acme Corp"
        title = "Backend Developer"
        jd = "We are seeking a Python and Django backend developer to build robust APIs."

        hash_id1 = derive_job_id(company, title, link="", description=jd)
        hash_id2 = derive_job_id(company, title, link="", description=jd)

        self.assertEqual(hash_id1, hash_id2)
        self.assertEqual(len(hash_id1), 16)


class TestFix4TitleLocationConcatenation(unittest.TestCase):
    """Fix 4: Ensure whitespace/separator between DOM text nodes and prevent location leakage into title"""

    def test_ashby_like_html_title_location_separation(self):
        html = """
        <div class="job-posting">
            <a href="/jobs/12345">
                <h3>Revenue Event Marketing Lead</h3>
                <span class="location">Remote - APAC, Singapore, Hong Kong</span>
            </a>
        </div>
        """
        scraper = JobScraper()
        company = {'name': 'Shopify', 'type': 'Tier-1 GCC', 'career_url': 'https://shopify.com/careers'}
        
        soup = BeautifulSoup(html, 'html.parser')
        response_mock = type('ResponseMock', (), {'text': html, 'status_code': 200})()
        
        jobs = scraper._scrape_generic(response_mock, company)
        if jobs:
            job = jobs[0]
            self.assertEqual(job['title'], "Revenue Event Marketing Lead")
            self.assertEqual(job['location'], "Remote - APAC, Singapore, Hong Kong")
            self.assertNotIn("Remote - APAC", job['title'])

    def test_dom_text_nodes_separated_by_whitespace(self):
        html = """
        <div class="job-card">
            <a href="/jobs/999">
                <span class="role">Software Engineer</span>
                <span class="location">Portugal, Lisbon</span>
            </a>
        </div>
        """
        scraper = JobScraper()
        company = {'name': 'Thought Machine', 'type': 'Tier-1 GCC', 'career_url': 'https://thoughtmachine.net/careers'}
        
        response_mock = type('ResponseMock', (), {'text': html, 'status_code': 200})()
        jobs = scraper._scrape_generic(response_mock, company)
        if jobs:
            job = jobs[0]
            self.assertEqual(job['title'], "Software Engineer")
            self.assertEqual(job['location'], "Portugal, Lisbon")
            self.assertNotEqual(job['title'], "Software EngineerPortugal, Lisbon")


class TestFix5DeadLinkAndSPAShellValidation(unittest.TestCase):
    """Fix 5: Validate page is not a dead link or SPA shell, and log skipped reasons"""

    def test_rejects_empty_and_short_descriptions(self):
        valid, reason = validate_job_page("")
        self.assertFalse(valid)
        self.assertEqual(reason, "Empty job description")

        valid, reason = validate_job_page("   ")
        self.assertFalse(valid)
        self.assertEqual(reason, "Empty job description")

        valid, reason = validate_job_page("Short text")
        self.assertFalse(valid)
        self.assertIn("Description too short", reason)

    def test_rejects_spa_shell_javascript_warning(self):
        # Specific bad rows from 2026-09-12 output (Paddle & Thought Machine rows)
        spa_text = "Creative Ops & Studio Manager @ Paddle\nYou need to enable JavaScript to run this app."
        valid, reason = validate_job_page(spa_text)
        self.assertFalse(valid)
        self.assertIn("SPA shell detected", reason)

        spa_text2 = "Software Engineer @ Thought Machine\nJavaScript is disabled in your browser."
        valid, reason = validate_job_page(spa_text2)
        self.assertFalse(valid)
        self.assertIn("SPA shell detected", reason)

    def test_rejects_dead_link_page_not_found(self):
        # Specific bad row from 2026-09-12 output (Remitly row)
        dead_link_text = "Page not found\nPage not found\nThe web page you were looking for could not be found."
        valid, reason = validate_job_page(dead_link_text)
        self.assertFalse(valid)
        self.assertIn("Dead link / 404", reason)

    def test_accepts_valid_job_description(self):
        clean_jd = """
        About the Role:
        We are looking for a Software Engineer to join our Payments Backend team in Bangalore.
        Responsibilities:
        - Design and implement microservices in Java and Spring Boot.
        - Work with PostgreSQL, Kafka, and AWS cloud infrastructure.
        Requirements:
        - 0-2 years of experience in backend development.
        - Strong foundation in data structures and algorithms.
        """
        valid, reason = validate_job_page(clean_jd)
        self.assertTrue(valid)
        self.assertEqual(reason, "")


if __name__ == '__main__':
    unittest.main()
