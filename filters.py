"""Job filtering logic based on experience, role type, location, and tech stack"""
import re
from config import (TARGET_LOCATIONS, BACKEND_KEYWORDS, EXCLUDE_KEYWORDS, 
                    TECH_STACK_KEYWORDS)

class JobFilter:
    @staticmethod
    def is_valid_location(location):
        if not location:
            return False
        location_lower = location.lower()
        return any(loc in location_lower for loc in TARGET_LOCATIONS)
    
    @staticmethod
    def is_backend_role(title, description):
        title_lower = title.lower()
        
        # Exclude unwanted roles only
        if any(kw in title_lower for kw in EXCLUDE_KEYWORDS):
            return False
        
        # Accept any software engineering role
        return True
    
    @staticmethod
    def extract_experience(title, description):
        text = f"{title} {description}".lower()
        
        # Pattern: 0-3, 0-2, 1-3, etc.
        pattern = r'(\d+)\s*[-to]+\s*(\d+)\s*(?:years?|yrs?)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            min_exp, max_exp = int(match[0]), int(match[1])
            if max_exp <= 3:
                return f"{min_exp}-{max_exp} years"
        
        # Check for "freshers" or "0 years"
        if any(word in text for word in ['fresher', 'fresh graduate', '0 year', 'entry level']):
            return "0-1 years"
        
        return "0-3 years"
    
    @staticmethod
    def is_valid_experience(title, description):
        text = f"{title} {description}".lower()
        
        # Reject if explicitly requires >3 years
        senior_patterns = [
            r'(\d+)\+\s*(?:years?|yrs?)',
            r'minimum\s+(\d+)\s+(?:years?|yrs?)',
            r'at least\s+(\d+)\s+(?:years?|yrs?)'
        ]
        
        for pattern in senior_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if int(match) > 3:
                    return False
        
        return True
    
    @staticmethod
    def has_relevant_tech_stack(description):
        # Accept all tech stacks - no constraint
        return True
    
    @staticmethod
    def filter_job(job):
        if not JobFilter.is_valid_location(job.get('location', '')):
            return False
        
        title = job.get('title', '')
        description = job.get('description', '')
        
        if not JobFilter.is_backend_role(title, description):
            return False
        
        if not JobFilter.is_valid_experience(title, description):
            return False
        
        return True
