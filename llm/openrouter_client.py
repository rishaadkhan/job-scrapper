"""OpenRouter API client with sequential model fallback and latency/attempt logging"""
import os
import time
import inspect
import logging
from typing import Optional, List, Tuple, Any, Dict, Union
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings, get_settings

logger = logging.getLogger("jobscraper.openrouter")

OPENROUTER_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


class BulletResult(tuple):
    """
    Result returned by generate_bullet containing the generated bullet text and serving model.
    Acts as a 2-tuple: (result, model_served).
    Provides property access (.result, .model), string conversion, and flexible equality.
    """
    def __new__(cls, result: Optional[str], model: Optional[str]):
        return super().__new__(cls, (result, model))

    @property
    def result(self) -> Optional[str]:
        return self[0]

    @property
    def model(self) -> Optional[str]:
        return self[1]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self[0] == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return self[0] or ""

    def __repr__(self) -> str:
        return f"BulletResult(result={self[0]!r}, model={self[1]!r})"


async def _record_attempt_log(
    db: Optional[AsyncSession],
    model_used: str,
    success: bool,
    latency_ms: float,
    purpose: str = "bullet_generation",
    error_message: Optional[str] = None
) -> None:
    """Safely persist LLM attempt record to llm_calls table without failing caller."""
    try:
        if db is not None:
            from backend.crud import log_llm_call
            await log_llm_call(
                db=db,
                model_used=model_used,
                success=success,
                latency_ms=latency_ms,
                purpose=purpose,
                error_message=error_message
            )
        else:
            from backend.database import AsyncSessionLocal
            from backend.crud import log_llm_call
            async with AsyncSessionLocal() as session:
                await log_llm_call(
                    db=session,
                    model_used=model_used,
                    success=success,
                    latency_ms=latency_ms,
                    purpose=purpose,
                    error_message=error_message
                )
    except Exception as exc:
        logger.debug(f"Could not record llm_calls metric to database: {exc}")


async def generate_bullet(
    snippet: str,
    jd_text: str,
    context: Optional[Any] = None,
    api_key: Optional[str] = None,
    model_priority: Optional[List[str]] = None,
    client: Optional[Any] = None,
    db: Optional[AsyncSession] = None,
    timeout_sec: float = 15.0
) -> BulletResult:
    """
    Generate tailored resume bullet points using OpenRouter with sequential model fallback.
    
    Tries each model in priority order:
    - Catches rate-limits (HTTP 429), server errors (5xx), timeouts, and client exceptions
    - Logs attempt successes, failures, and latencies
    - Inserts a record into llm_calls per attempt for observability
    - Returns BulletResult(result, model_served)
    
    If OPENROUTER_API_KEY is unset or empty:
    - Logs "Resume tailoring: DISABLED"
    - Returns BulletResult("disabled", None) cleanly without raising.
    """
    cfg = settings
    key = api_key if api_key is not None else (cfg.OPENROUTER_API_KEY if cfg else os.getenv("OPENROUTER_API_KEY", ""))

    if not key or not str(key).strip():
        logger.info("Resume tailoring: DISABLED")
        return BulletResult("disabled", None)

    # Determine ordered model list
    if model_priority:
        models = [m.strip() for m in model_priority if m.strip()]
    elif cfg and cfg.OPENROUTER_MODEL_PRIORITY:
        models = cfg.OPENROUTER_MODEL_PRIORITY
    else:
        raw_env = os.getenv("OPENROUTER_MODEL_PRIORITY", "anthropic/claude-3.5-sonnet,openai/gpt-4o-mini")
        models = [m.strip() for m in raw_env.split(",") if m.strip()]

    if not models:
        models = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jobscraper.io",
        "X-Title": "Job Scraper Enterprise"
    }

    prompt_context = f"\nAdditional Context: {context}" if context else ""
    user_prompt = (
        f"Job Description:\n{jd_text}\n\n"
        f"Original Resume Achievement / Bullet Snippet:\n{snippet}"
        f"{prompt_context}\n\n"
        "Tailor and rewrite the snippet for this specific job posting. "
        "Return 1-2 concise, high-impact bullet points beginning with strong action verbs. "
        "Do NOT include markdown headers, quotes, or conversational preamble."
    )

    for idx, model_slug in enumerate(models):
        start_time = time.perf_counter()
        payload = {
            "model": model_slug,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an elite technical resume coach and executive software engineering recruiter."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }

        try:
            # Execute request via provided client or new AsyncClient
            if client is not None:
                if inspect.iscoroutinefunction(client.post):
                    response = await client.post(OPENROUTER_COMPLETIONS_URL, headers=headers, json=payload, timeout=timeout_sec)
                else:
                    call_res = client.post(OPENROUTER_COMPLETIONS_URL, headers=headers, json=payload, timeout=timeout_sec)
                    response = await call_res if inspect.isawaitable(call_res) else call_res
            else:
                async with httpx.AsyncClient(timeout=timeout_sec) as temp_client:
                    response = await temp_client.post(OPENROUTER_COMPLETIONS_URL, headers=headers, json=payload)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            status_code = getattr(response, "status_code", None)

            # Handle Rate Limits (429)
            if status_code == 429:
                logger.warning(
                    f"OpenRouter model '{model_slug}' returned 429 (Rate Limit Exceeded). "
                    f"Latency: {latency_ms}ms. Attempting next fallback model in priority list..."
                )
                await _record_attempt_log(
                    db=db,
                    model_used=model_slug,
                    success=False,
                    latency_ms=latency_ms,
                    purpose="bullet_generation",
                    error_message="HTTP 429: Rate limit exceeded"
                )
                continue

            # Handle Server Errors (5xx)
            if status_code and status_code >= 500:
                logger.warning(
                    f"OpenRouter model '{model_slug}' returned server error {status_code}. "
                    f"Latency: {latency_ms}ms. Attempting next fallback model..."
                )
                await _record_attempt_log(
                    db=db,
                    model_used=model_slug,
                    success=False,
                    latency_ms=latency_ms,
                    purpose="bullet_generation",
                    error_message=f"HTTP {status_code}: Server error"
                )
                continue

            # Handle Client Errors (4xx other than 429)
            if status_code and status_code >= 400 and status_code != 429:
                logger.warning(
                    f"OpenRouter model '{model_slug}' returned client error {status_code}: {getattr(response, 'text', '')}. "
                    f"Attempting fallback..."
                )
                await _record_attempt_log(
                    db=db,
                    model_used=model_slug,
                    success=False,
                    latency_ms=latency_ms,
                    purpose="bullet_generation",
                    error_message=f"HTTP {status_code}: Client error"
                )
                continue

            # Handle Successful Response
            data = response.json() if hasattr(response, "json") else {}
            choices = data.get("choices", [])
            content_text = ""
            if choices and isinstance(choices, list):
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    msg = first_choice.get("message", {})
                    content_text = msg.get("content", "").strip()

            logger.info(f"OpenRouter model '{model_slug}' succeeded in {latency_ms:.1f}ms")
            await _record_attempt_log(
                db=db,
                model_used=model_slug,
                success=True,
                latency_ms=latency_ms,
                purpose="bullet_generation",
                error_message=None
            )
            return BulletResult(content_text, model_slug)

        except (httpx.TimeoutException, TimeoutError) as timeout_exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(
                f"OpenRouter model '{model_slug}' timed out after {latency_ms}ms. "
                "Attempting next model in priority order..."
            )
            await _record_attempt_log(
                db=db,
                model_used=model_slug,
                success=False,
                latency_ms=latency_ms,
                purpose="bullet_generation",
                error_message="Subprocess/HTTP Timeout"
            )
            continue

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(
                f"OpenRouter model '{model_slug}' failed with exception ({type(exc).__name__}: {str(exc)}). "
                "Attempting next model..."
            )
            await _record_attempt_log(
                db=db,
                model_used=model_slug,
                success=False,
                latency_ms=latency_ms,
                purpose="bullet_generation",
                error_message=f"{type(exc).__name__}: {str(exc)}"
            )
            continue

    logger.error(f"All {len(models)} OpenRouter models in priority list failed.")
    return BulletResult(None, None)
