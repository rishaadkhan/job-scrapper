"""
Anthropic Claude API client for generating tailored resume bullet suggestions.
Designed for graceful degradation: missing API key, timeouts, rate limits, or
network failures will log a warning and return an empty string without failing the pipeline.
"""
import os
import logging
from typing import Optional, List
import httpx
from config.settings import settings

logger = logging.getLogger("jobscraper.scoring.bullets")


class BulletGenerator:
    """Generates tailored resume bullet points for high-scoring leads via Anthropic API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        threshold: Optional[int] = None
    ):
        cfg_key = settings.ANTHROPIC_API_KEY if settings else os.getenv("ANTHROPIC_API_KEY", "")
        cfg_model = settings.ANTHROPIC_MODEL if settings else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        cfg_threshold = settings.LLM_SUGGESTION_THRESHOLD if settings else int(os.getenv("LLM_SUGGESTION_THRESHOLD", "60"))

        self.api_key = api_key if api_key is not None else cfg_key
        self.model = model or cfg_model or "claude-3-5-sonnet-latest"
        self.threshold = threshold if threshold is not None else cfg_threshold

    async def generate_bullets(
        self,
        company: str,
        title: str,
        description: str,
        resume_text: str,
        top_keywords: List[str],
        missing_keywords: List[str],
        match_score: int,
        client: Optional[httpx.AsyncClient] = None
    ) -> str:
        """
        Generates 2-3 tailored bullet points if match_score >= threshold.
        Gracefully returns empty string on missing key, low score, or API failure.
        """
        if match_score < self.threshold:
            return ""

        if not self.api_key or not self.api_key.strip():
            logger.debug(f"Skipping bullet generation for '{title}' at '{company}': ANTHROPIC_API_KEY not set.")
            return ""

        prompt = f"""You are an elite technical resume strategist.
Generate 2-3 high-impact, tailored resume bullet points that the candidate can use when applying for this role.

Role: {title} at {company}
Top Emphasized Skills: {', '.join(top_keywords[:8])}
Missing/Skills to Highlight: {', '.join(missing_keywords[:5]) if missing_keywords else 'None'}

Job Description Summary:
{description[:1500]}

Candidate Resume Context:
{resume_text[:1500]}

Instructions:
1. Write exactly 2-3 bullet points starting with '• '.
2. Use strong action verbs, mention key technologies ({', '.join(top_keywords[:5])}), and emphasize scalable engineering impact.
3. Output ONLY the bullet points, no commentary or conversational filler.
"""

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 400,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        url = "https://api.anthropic.com/v1/messages"

        try:
            if client:
                response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            else:
                async with httpx.AsyncClient(timeout=15.0) as temp_client:
                    response = await temp_client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                content_blocks = data.get("content", [])
                if content_blocks and isinstance(content_blocks, list):
                    text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    return "\n".join(text_parts).strip()
                return ""
            elif response.status_code == 429:
                logger.warning(f"Anthropic API rate limit exceeded (429) for '{company}' — continuing with empty bullets.")
                return ""
            elif response.status_code in (401, 403):
                logger.warning(f"Anthropic API authentication failed ({response.status_code}) — check ANTHROPIC_API_KEY. Continuing with empty bullets.")
                return ""
            else:
                logger.warning(f"Anthropic API returned status {response.status_code} for '{company}' — continuing with empty bullets.")
                return ""

        except httpx.TimeoutException:
            logger.warning(f"Anthropic API call timed out for '{company}' — continuing pipeline with empty bullets.")
            return ""
        except Exception as exc:
            logger.warning(f"Could not generate bullets for '{company}' ({type(exc).__name__}: {str(exc)}) — continuing pipeline with empty bullets.")
            return ""
