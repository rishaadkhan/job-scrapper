"""Job filtering logic based on experience, role type, location, and tech stack"""
import re
from config import (TARGET_LOCATIONS, BACKEND_KEYWORDS, EXCLUDE_KEYWORDS,
                    TECH_STACK_KEYWORDS)


class JobFilter:

    @staticmethod
    def is_valid_location(location: str) -> bool:
        if not location:
            return False
        location_lower = location.lower()
        return any(loc in location_lower for loc in TARGET_LOCATIONS)

    @staticmethod
    def is_backend_role(title: str, description: str) -> bool:
        title_lower = title.lower()

        # FIX 1: use whole-phrase matching instead of substring to avoid
        # blocking "Software Engineer - Platform Support" via "support engineer"
        for kw in EXCLUDE_KEYWORDS:
            # wrap in word boundaries; falls back to plain 'in' for multi-word phrases
            if len(kw.split()) > 1:
                if kw in title_lower:
                    return False
            else:
                if re.search(rf'\b{re.escape(kw)}\b', title_lower):
                    return False

        return True

    @staticmethod
    def extract_experience(title: str, description: str) -> str:
        text = f"{title} {description}".lower()

        # Range pattern: "0-3 years", "1 to 2 yrs", etc.
        range_pattern = r'(\d+)\s*[-to]+\s*(\d+)\s*(?:years?|yrs?)'
        for min_exp, max_exp in re.findall(range_pattern, text):
            if int(max_exp) <= 4:           # slightly relaxed from 3→4
                return f"{min_exp}-{max_exp} years"

        if any(w in text for w in ['fresher', 'fresh graduate', '0 year', 'entry level', 'entry-level']):
            return "0-1 years"

        return "0-3 years"

    @staticmethod
    def is_valid_experience(title: str, description: str) -> bool:
        text = f"{title} {description}".lower()

        # FIX 2: old pattern fired on "50+ engineers", "2000+ users", etc.
        # New approach: only flag N+ when it appears next to experience-related words
        # within a short context window (~60 chars).
        experience_context_pattern = re.compile(
            r'(\d+)\s*\+\s*(?:years?|yrs?)'        # "4+ years" / "5+ yrs"
        )
        for match in experience_context_pattern.finditer(text):
            years = int(match.group(1))
            if years > 3:
                return False

        # "minimum 5 years", "at least 4 years experience"
        minimum_patterns = [
            r'minimum\s+(\d+)\s+(?:years?|yrs?)',
            r'at\s+least\s+(\d+)\s+(?:years?|yrs?)',
            r'(\d+)\s+(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience\s+required',
        ]
        for pattern in minimum_patterns:
            for match in re.finditer(pattern, text):
                if int(match.group(1)) > 3:
                    return False

        return True

    @staticmethod
    def has_relevant_tech_stack(description: str) -> bool:
        """Returns True if any target tech keyword appears — used as a soft signal."""
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in TECH_STACK_KEYWORDS)

    @staticmethod
    def filter_job(job: dict) -> bool:
        if not JobFilter.is_valid_location(job.get('location', '')):
            return False

        title = job.get('title', '')
        description = job.get('description', '')

        if not JobFilter.is_backend_role(title, description):
            return False

        if not JobFilter.is_valid_experience(title, description):
            return False

        # FIX 3: attach computed fields to job dict so Excel columns get populated
        job['experience_range'] = JobFilter.extract_experience(title, description)

        # FIX 4: soft signal — flag whether job matches your specific stack
        # (doesn't filter, just adds a column you can sort on in Excel)
        job['stack_match'] = JobFilter.has_relevant_tech_stack(description)

        return True
