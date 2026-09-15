"""Job filtering logic based on experience, role type, location, and tech stack"""
import re
from config import (TARGET_LOCATIONS, BACKEND_KEYWORDS, EXCLUDE_KEYWORDS,
                    TECH_STACK_KEYWORDS)

DISQUALIFYING_LOCATIONS = [
    # Non-India countries
    "united states", "usa", "us", "canada", "mexico", "united kingdom", "uk",
    "germany", "ireland", "netherlands", "france", "poland", "portugal",
    "spain", "switzerland", "sweden", "norway", "denmark", "finland",
    "singapore", "hong kong", "japan", "australia", "new zealand",
    "philippines", "vietnam", "china", "taiwan", "south korea", "brazil",
    "uae", "dubai", "israel",
    # Non-India cities & states
    "vancouver", "toronto", "montreal", "ottawa", "calgary",
    "seattle", "san francisco", "sf", "new york", "nyc", "austin", "boston",
    "chicago", "los angeles", "london", "lisbon", "dublin", "berlin",
    "amsterdam", "paris", "tokyo", "sydney", "melbourne",
    # Regions
    "apac", "emea", "latam", "north america", "europe"
]

INDIA_INDICATORS = [
    "india", "bangalore", "bengaluru", "hyderabad", "pune", "chennai",
    "delhi", "ncr", "gurgaon", "gurugram", "noida", "mumbai", "navi mumbai",
    "kolkata", "ahmedabad"
]


class JobFilter:

    @staticmethod
    def is_valid_location(location: str, description: str = "", location_filter: list = None) -> bool:
        """Validate location from scraped location field or JD text. Never validates against URL."""
        if not location and not description:
            return False

        loc_str = location.lower().strip() if location else ""
        targets = [t.lower() for t in (location_filter or TARGET_LOCATIONS)]

        if loc_str:
            # 1. Disqualifying non-India location check
            has_disqualifier = False
            for disq in DISQUALIFYING_LOCATIONS:
                if len(disq) <= 3:
                    if re.search(rf'\b{re.escape(disq)}\b', loc_str):
                        has_disqualifier = True
                        break
                else:
                    if disq in loc_str:
                        has_disqualifier = True
                        break

            # Check for US state abbreviation patterns like ", WA", ", CA", etc.
            if re.search(r',\s*(wa|ca|ny|tx|ma|il|fl|nc|co|va|or|nj|pa|ga|oh|mi)\b', loc_str):
                has_disqualifier = True

            # If location has non-India signals and lacks explicit India indicators, reject immediately
            has_explicit_india = any(
                re.search(rf'\b{re.escape(ind)}\b', loc_str) if len(ind) <= 3 else ind in loc_str
                for ind in INDIA_INDICATORS
            )

            if has_disqualifier and not has_explicit_india:
                return False

            # 2. Positive target match
            has_target = False
            for target in targets:
                if len(target) <= 3:
                    if re.search(rf'\b{re.escape(target)}\b', loc_str):
                        has_target = True
                        break
                else:
                    if target in loc_str:
                        has_target = True
                        break

            if has_target:
                return True

            return False

        # If location field was empty, check description text for India location signals
        desc_lower = description.lower()
        has_target_in_desc = any(
            re.search(rf'\b{re.escape(target)}\b', desc_lower) if len(target) <= 3 else target in desc_lower
            for target in targets if target != "remote"
        )
        has_disq_in_desc = any(
            re.search(rf'\b{re.escape(disq)}\b', desc_lower) if len(disq) <= 3 else disq in desc_lower
            for disq in DISQUALIFYING_LOCATIONS
        )

        has_explicit_india_in_desc = any(
            re.search(rf'\b{re.escape(ind)}\b', desc_lower) if len(ind) <= 3 else ind in desc_lower
            for ind in INDIA_INDICATORS
        )

        if has_target_in_desc and (not has_disq_in_desc or has_explicit_india_in_desc):
            return True

        return False

    @staticmethod
    def is_backend_role(title: str, description: str = "") -> bool:
        """Positively requires BACKEND_KEYWORDS match and absence of EXCLUDE_KEYWORDS."""
        if not title:
            return False
        title_lower = title.lower()

        # 1. Exclusion check on title
        for kw in EXCLUDE_KEYWORDS:
            if len(kw.split()) > 1:
                if kw in title_lower:
                    return False
            else:
                if re.search(rf'\b{re.escape(kw)}\b', title_lower):
                    return False

        # 2. Positive requirement: check BACKEND_KEYWORDS in title
        for kw in BACKEND_KEYWORDS:
            if len(kw.split()) > 1:
                if kw in title_lower:
                    return True
            else:
                if re.search(rf'\b{re.escape(kw)}\b', title_lower):
                    return True

        # If title did not match directly, check description if provided
        if description:
            desc_lower = description.lower()
            # Non-tech roles shouldn't pass even if their JD mentions software keywords
            non_tech_terms = [
                "marketing", "sales", "revenue", "ops", "operations", "studio",
                "recruiter", "hr", "legal", "finance", "accountant"
            ]
            if any(re.search(rf'\b{re.escape(term)}\b', title_lower) for term in non_tech_terms):
                return False

            for kw in BACKEND_KEYWORDS:
                pattern = rf'\b{re.escape(kw)}\b' if len(kw.split()) == 1 else re.escape(kw)
                if re.search(pattern, desc_lower):
                    return True

        return False

    @staticmethod
    def extract_experience(title: str, description: str) -> str:
        text = f"{title} {description}".lower()

        # Range pattern: "0-3 years", "1 to 2 yrs", etc.
        range_pattern = r'(\d+)\s*[-to]+\s*(\d+)\s*(?:years?|yrs?)'
        for min_exp, max_exp in re.findall(range_pattern, text):
            if int(max_exp) <= 4:
                return f"{min_exp}-{max_exp} years"

        if any(w in text for w in ['fresher', 'fresh graduate', '0 year', 'entry level', 'entry-level']):
            return "0-1 years"

        return "0-3 years"

    @staticmethod
    def is_valid_experience(title: str, description: str) -> bool:
        text = f"{title} {description}".lower()

        experience_context_pattern = re.compile(
            r'(\d+)\s*\+\s*(?:years?|yrs?)'
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
    def filter_job(job: dict, company: dict = None) -> bool:
        location_filter = company.get('location_filter') if company else None
        location = job.get('location', '')
        description = job.get('description', '')
        title = job.get('title', '')

        if not JobFilter.is_valid_location(location, description, location_filter):
            return False

        if not JobFilter.is_backend_role(title, description):
            return False

        if not JobFilter.is_valid_experience(title, description):
            return False

        job['experience_range'] = JobFilter.extract_experience(title, description)
        job['stack_match'] = JobFilter.has_relevant_tech_stack(description)

        return True
