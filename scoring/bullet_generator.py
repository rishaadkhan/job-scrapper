"""Anthropic Claude API client for generating tailored resume bullet suggestions"""
import os
from typing import Optional, List
import httpx
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, LLM_SUGGESTION_THRESHOLD


class BulletGenerator:
    """Generates tailored resume bullet points for high-scoring leads via Anthropic API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        threshold: Optional[int] = None
    ):
        self.api_key = api_key if api_key is not None else ANTHROPIC_API_KEY
        self.model = model or ANTHROPIC_MODEL or "claude-3-5-sonnet-latest"
        self.threshold = threshold if threshold is not None else LLM_SUGGESTION_THRESHOLD

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

        if not self.api_key:
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
                response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            else:
                async with httpx.AsyncClient(timeout=20.0) as temp_client:
                    response = await temp_client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                content_blocks = data.get("content", [])
                if content_blocks and isinstance(content_blocks, list):
                    text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    return "\n".join(text_parts).strip()
            else:
                print(f"  [LLM Warning] Anthropic API returned status {response.status_code} for {company}")
                return ""

        except Exception as e:
            print(f"  [LLM Warning] Could not generate bullets for {company}: {str(e)}")
            return ""

        return ""
