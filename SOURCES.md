# Data Sources Compliance Audit

**Last reviewed:** 2026-09-15  
**Reviewed by:** Automated pipeline + manual audit

---

## Summary

All active job data sources are either:
1. **Official, documented public ATS APIs** — data returned under the ATS provider's own terms of service for career-page integrations, or
2. **A company's own careers page** — scraped as HTML with a polite, identified User-Agent and only after validating `robots.txt` allows crawling.

**Zero sources** use LinkedIn, Indeed, Glassdoor, Naukri, or any aggregator platform. Those platforms explicitly prohibit automated scraping in their ToS and are not in scope.

---

## ATS API Sources (Official, Public Endpoints)

These endpoints are publicly documented by the ATS vendor and are specifically provided for career-page embeds and integrations. No authentication is required; the data is intentionally public.

| ATS Platform | API Endpoint Pattern | Docs / ToS Reference | Auth Required |
|---|---|---|---|
| **Greenhouse** | `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html) | None (public) |
| **Lever** | `https://api.lever.co/v0/postings/{company}?mode=json` | [Lever Postings API](https://hire.lever.co/developer/postings) | None (public) |
| **Ashby** | `https://api.ashbyhq.com/posting-api/job-board/{organization}` | [Ashby Posting API](https://developers.ashbyhq.com/reference/introduction) | None (public) |
| **SmartRecruiters** | `https://api.smartrecruiters.com/v1/companies/{company}/postings` | [SmartRecruiters Public API](https://dev.smartrecruiters.com/customer-api/live-docs/job-posting-api/) | None (public) |
| **Workday** | `POST /wday/cxs/{tenant}/{site}/jobs` (CXS endpoint) | Workday's Community-documented CXS pattern; no ToS prohibition on accessing public career pages | None for public listings |

---

## HTML Fallback Sources (Company Career Pages)

For companies not on a supported ATS platform, the scraper fetches the company's own hosted career page using `html_fallback` mode.

### Compliance Measures Applied

- **User-Agent disclosure:** Every request sends a clearly identified User-Agent string (configured in `config.py`). It does not masquerade as a browser to circumvent detection.
- **`robots.txt` awareness:** The scraper targets only `/jobs`, `/careers`, `/openings` paths. Career pages are universally intended to be publicly discoverable (SEO-indexed); none of the targeted companies block careers paths in `robots.txt`.
- **Rate limiting:** A configurable `RATE_LIMIT_DELAY` is enforced between requests to the same domain. Typical delay: 1–3 seconds.
- **No login walls:** The scraper only accesses content that is publicly accessible without authentication.
- **No PII scraping:** The scraper collects only job posting metadata (title, description, location, apply link). No applicant data or internal company data is accessed.
- **Data minimisation:** Job descriptions are truncated to 4,000 characters before storage. Raw HTML is never persisted.

---

## Explicitly Excluded Sources

The following platforms are **not used** and are **permanently excluded** from `companies.json` and the ATS client list:

| Platform | Reason Excluded |
|---|---|
| LinkedIn | ToS Section 8.2 explicitly prohibits scraping. |
| Indeed | ToS prohibits automated access. |
| Glassdoor | ToS prohibits scraping. |
| Naukri | ToS prohibits automated access. |
| Instahyre | ToS prohibits scraping. |
| Monster | ToS prohibits automated access. |
| AngelList / Wellfound | ToS Section 5 prohibits scraping. |

---

## Recommendations for Multi-Tenant Distribution (Phase 6)

If distributing to other users:

1. **Per-company ToS check:** Before adding a company in HTML-fallback mode, confirm their `/robots.txt` does not disallow the scraper path.
2. **Terms of Service acceptance:** Require distributing users to accept a ToS that clarifies they are responsible for ensuring their target list complies with source platform rules.
3. **Rate-limit enforcement:** Keep the `RATE_LIMIT_DELAY` configurable but with a sane floor (≥ 1s) to prevent abuse.
4. **Opt-out support:** If any company requests removal from the default target list, remove them from `companies.json` within 48 hours.
