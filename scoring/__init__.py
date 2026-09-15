"""Scoring and Resume Intelligence Module"""
from typing import Dict, Any, Optional
import httpx
from .taxonomy import BACKEND_TAXONOMY, CANONICAL_SKILL_MAP
from .extractor import KeywordExtractor
from .matcher import ResumeMatcher
from .bullet_generator import BulletGenerator
from config import RESUME_FILE


class JobScorer:
    """Coordinates resume matching, skill extraction, match scoring, and bullet generation."""

    def __init__(self, resume_path: str = RESUME_FILE):
        self.matcher = ResumeMatcher(resume_path=resume_path)
        self.bullet_generator = BulletGenerator()

    async def score_and_enrich_job(self, job: Dict[str, Any], client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
        """
        Enriches a job dictionary with:
        - match_score: int (0-100)
        - top_jd_keywords: List[str]
        - missing_from_resume: List[str]
        - suggested_bullets: str
        """
        title = job.get('title', '')
        description = job.get('description', '')
        company = job.get('company', '')

        score_res = self.matcher.score_job(title, description)

        match_score = score_res['match_score']
        top_keywords = score_res['top_jd_keywords']
        missing_keywords = score_res['missing_from_resume']

        job['match_score'] = match_score
        job['top_jd_keywords'] = top_keywords
        job['missing_from_resume'] = missing_keywords

        # Generate LLM bullets if applicable
        suggested_bullets = await self.bullet_generator.generate_bullets(
            company=company,
            title=title,
            description=description,
            resume_text=self.matcher.resume_text,
            top_keywords=top_keywords,
            missing_keywords=missing_keywords,
            match_score=match_score,
            client=client
        )
        job['suggested_bullets'] = suggested_bullets

        return job


__all__ = [
    'JobScorer',
    'KeywordExtractor',
    'ResumeMatcher',
    'BulletGenerator',
    'BACKEND_TAXONOMY',
    'CANONICAL_SKILL_MAP'
]
