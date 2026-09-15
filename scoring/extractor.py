"""Keyword extraction and TF-IDF frequency scoring over job descriptions"""
import re
from collections import Counter
from typing import List, Dict, Tuple, Set
from .taxonomy import CANONICAL_SKILL_MAP, get_all_taxonomy_terms


class KeywordExtractor:
    """Extracts top emphasized backend skills from job title and description text."""

    def __init__(self):
        self.terms = get_all_taxonomy_terms()

    def _extract_term_matches(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Finds all taxonomy term matches in text using maximal munch
        (longer phrases take precedence over substrings, e.g. 'Spring Boot' over 'Spring').
        Returns list of (canonical_name, start_idx, end_idx).
        """
        if not text:
            return []

        text_lower = text.lower()
        matched_spans: List[Tuple[int, int]] = []
        term_matches: List[Tuple[str, int, int]] = []

        for term in self.terms:
            canonical = CANONICAL_SKILL_MAP[term]

            if len(term) <= 3 or term in ["c++", "c#", "go", "sql", "aws", "gcp", "k8s", "oop", "tdd", "etl"]:
                pattern = rf'(?<![a-zA-Z0-9]){re.escape(term)}(?![a-zA-Z0-9])'
            else:
                pattern = rf'\b{re.escape(term)}\b'

            for m in re.finditer(pattern, text_lower):
                start, end = m.start(), m.end()

                # Check if this span overlaps with an already matched longer phrase
                overlapping = False
                for prev_start, prev_end in matched_spans:
                    if not (end <= prev_start or start >= prev_end):
                        overlapping = True
                        break

                if not overlapping:
                    matched_spans.append((start, end))
                    term_matches.append((canonical, start, end))

        return term_matches

    def extract_keywords(self, title: str, description: str, top_n: int = 10) -> List[str]:
        """
        Extracts the top N emphasized keywords from the job title and description.
        Returns a list of canonical skill names in descending order of relevance.
        """
        title_text = title or ""
        desc_text = description or ""

        scores: Counter = Counter()

        # 1. Title prominence (weight: 4.0)
        title_matches = self._extract_term_matches(title_text)
        for canonical, _, _ in title_matches:
            scores[canonical] += 4.0

        # 2. Requirements section prominence (weight: 2.5)
        desc_lower = desc_text.lower()
        req_match = re.search(
            r'(requirements|qualifications|what you bring|what you need|skills required|must have)(.*?)(responsibilities|what you will do|benefits|about us|$)',
            desc_lower,
            re.DOTALL
        )
        if req_match:
            req_text = desc_text[req_match.start(2):req_match.end(2)]
            req_matches = self._extract_term_matches(req_text)
            for canonical, _, _ in req_matches:
                scores[canonical] += 2.5

        # 3. Overall JD frequency (weight: 1.0)
        body_matches = self._extract_term_matches(desc_text)
        for canonical, _, _ in body_matches:
            scores[canonical] += 1.0

        if not scores:
            return []

        # Return top N ranked by score
        top_skills = [skill for skill, score in scores.most_common(top_n)]
        return top_skills
