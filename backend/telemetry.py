"""
Observability bootstrapping: Sentry error tracking and job heartbeat.

Both integrations are entirely optional — if the corresponding environment
variables are absent the functions are no-ops so the pipeline runs unchanged.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger("jobscraper.telemetry")


def init_sentry() -> None:
    """
    Initialise Sentry SDK if SENTRY_DSN is configured.

    For FastAPI, the sentry-sdk[fastapi] extra patches the ASGI middleware
    automatically once init() is called, so no manual middleware registration
    is needed.
    """
    dsn: str = os.getenv("SENTRY_DSN", "")
    if not dsn:
        logger.debug("SENTRY_DSN not set — Sentry integration skipped")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        environment = os.getenv("ENVIRONMENT", "production")
        release = os.getenv("GIT_SHA", "unknown")

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            # Capture 5 % of transactions for performance profiling
            traces_sample_rate=0.05,
            # Only forward ERROR and above to Sentry; WARNING stays local
            integrations=[
                LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR),
                SqlalchemyIntegration(),
            ],
            # Strip PII from payloads
            send_default_pii=False,
        )
        logger.info(f"Sentry initialised (env={environment}, release={release})")
    except ImportError:
        logger.warning("sentry-sdk not installed — install it with: pip install sentry-sdk[fastapi]")
    except Exception as exc:
        # Never let observability bootstrap crash the application
        logger.warning(f"Sentry init failed (non-fatal): {exc}")


def send_heartbeat(url: Optional[str] = None) -> None:
    """
    Ping a healthchecks.io (or compatible) heartbeat URL to confirm a scrape
    run completed successfully.

    Set HEARTBEAT_URL to your healthchecks.io ping URL, e.g.:
        https://hc-ping.com/<uuid>

    A missing or empty URL is silently skipped so local runs are unaffected.
    """
    heartbeat_url: str = url or os.getenv("HEARTBEAT_URL", "")
    if not heartbeat_url:
        return

    import urllib.request
    try:
        with urllib.request.urlopen(heartbeat_url, timeout=10) as resp:
            logger.info(f"Heartbeat sent → {heartbeat_url} (HTTP {resp.status})")
    except Exception as exc:
        # Heartbeat failure must never abort the main pipeline
        logger.warning(f"Heartbeat ping failed (non-fatal): {exc}")
