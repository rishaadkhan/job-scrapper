"""Resume parsing, keyword intersection, and 0-100 Match Score computation"""
import os
from typing import List, Set, Dict, Any, Tuple
from .taxonomy import CANONICAL_SKILL_MAP, get_all_taxonomy_terms
from .extractor import KeywordExtractor


class ResumeMatcher:
    """Matches job descriptions against a candidate's resume and scores alignment."""

    def __init__(self, resume_path: str = "resume.md"):
        self.resume_path = resume_path
        self.extractor = KeywordExtractor()
        self.resume_text = self._load_resume(resume_path)
        self.resume_keywords = self._extract_resume_skills(self.resume_text)

    def _load_resume(self, path: str) -> str:
        if not path or not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not read resume at {path}: {str(e)}")
            return ""

    def _extract_resume_skills(self, text: str) -> Set[str]:
        if not text:
            return set()
        # Extract all taxonomy skills present in the resume
        skills = self.extractor.extract_keywords(title="Resume", description=text, top_n=100)
        return set(skills)

    def score_job(self, title: str, description: str) -> Dict[str, Any]:
        """
        Extracts top JD keywords, matches against resume keywords,
        and computes a 0-100 match score with missing keyword analysis.
        """
        top_jd_keywords = self.extractor.extract_keywords(title, description, top_n=10)

        if not top_jd_keywords:
            return {
                'match_score': 50,
                'top_jd_keywords': [],
                'matched_keywords': [],
                'missing_from_resume': []
            }

        matched = [kw for kw in top_jd_keywords if kw in self.resume_keywords]
        missing = [kw for kw in top_jd_keywords if kw not in self.resume_keywords]

        # Base score from top keyword overlap
        if len(top_jd_keywords) > 0:
            raw_score = (len(matched) / len(top_jd_keywords)) * 100
        else:
            raw_score = 50.0

        # If resume had 0 keywords loaded (no resume provided), provide baseline 50
        if not self.resume_keywords:
            match_score = 50
        else:
            match_score = int(round(raw_score))

        match_score = max(0, min(100, match_score))

        return {
            'match_score': match_score,
            'top_jd_keywords': top_jd_keywords,
            'matched_keywords': matched,
            'missing_from_resume': missing
        }
