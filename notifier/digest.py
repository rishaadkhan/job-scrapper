"""
Daily digest notifier — sends a Telegram message (primary) or email (fallback)
summarising the top N job matches after each scrape run.

Environment variables
─────────────────────
TELEGRAM_BOT_TOKEN   Token from @BotFather; if absent, falls back to email
TELEGRAM_CHAT_ID     Your personal / group chat ID (use @userinfobot to find)
DIGEST_SCORE_THRESHOLD  Minimum match score to include in digest (default: 60)
DIGEST_TOP_N            Maximum jobs to list (default: 10)

SMTP_HOST            e.g. smtp.gmail.com
SMTP_PORT            e.g. 587
SMTP_USER            Sending address
SMTP_PASSWORD        App password / SMTP credential
SMTP_TO              Recipient address

Usage
─────
    from notifier.digest import send_daily_digest
    await send_daily_digest(valid_jobs=all_valid_jobs, run_id=42)

CLI dry-run:
    python -m notifier.digest --dry-run
"""

import asyncio
import logging
import os
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("jobscraper.notifier")

# ── Configuration ─────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
DIGEST_SCORE_THRESHOLD: int = int(os.getenv("DIGEST_SCORE_THRESHOLD", "60"))
DIGEST_TOP_N: int = int(os.getenv("DIGEST_TOP_N", "10"))

SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_TO: str = os.getenv("SMTP_TO", "")


# ── Message formatting ─────────────────────────────────────────────────────────

def _escape_telegram(text: str) -> str:
    """Escape MarkdownV2 special characters as required by the Telegram Bot API."""
    # Characters that must be escaped in MarkdownV2
    for ch in r"_*[]()~`>#+-=|{}.!\\":
        text = text.replace(ch, f"\\{ch}")
    return text


def _build_telegram_message(jobs: List[Dict[str, Any]], run_id: Optional[int]) -> str:
    """
    Format the top-N jobs as a Telegram MarkdownV2 message.

    Each entry shows: rank, company, title, score, apply link.
    """
    n = len(jobs)
    run_label = f"Run \\#{run_id}" if run_id else "Latest run"
    header = (
        f"🔍 *Job Scraper Daily Digest* — {run_label}\n"
        f"📊 *{n} high\\-match lead{'s' if n != 1 else ''}* \\(score ≥ {DIGEST_SCORE_THRESHOLD}\\)\n\n"
    )

    lines = []
    for i, job in enumerate(jobs, 1):
        score = job.get("match_score", 0)
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        title = _escape_telegram(job.get("title", "Unknown Role"))
        company = _escape_telegram(job.get("company", job.get("company_name", "Unknown")))
        link = job.get("link", job.get("apply_link", ""))
        skills = ", ".join(job.get("top_jd_keywords", [])[:4]) or "—"
        skills = _escape_telegram(skills)

        entry = f"{emoji} *{i}\\. {title}*\n   📍 {company} · Score: `{score}/100`\n   🛠 {skills}"
        if link:
            entry += f"\n   [Apply →]({link})"
        lines.append(entry)

    footer = "\n\n_Sent by Job Scraper Enterprise_"
    return header + "\n\n".join(lines) + footer


def _build_email_body(jobs: List[Dict[str, Any]], run_id: Optional[int]) -> str:
    """Format a plain-text email body for the digest."""
    n = len(jobs)
    run_label = f"Run #{run_id}" if run_id else "Latest run"
    lines = [
        f"Job Scraper Daily Digest — {run_label}",
        f"{n} high-match lead{'s' if n != 1 else ''} (score >= {DIGEST_SCORE_THRESHOLD})",
        "=" * 60,
        "",
    ]
    for i, job in enumerate(jobs, 1):
        score = job.get("match_score", 0)
        title = job.get("title", "Unknown Role")
        company = job.get("company", job.get("company_name", "Unknown"))
        link = job.get("link", job.get("apply_link", ""))
        skills = ", ".join(job.get("top_jd_keywords", [])[:5]) or "—"
        lines += [
            f"{i}. {title} @ {company}",
            f"   Score: {score}/100",
            f"   Top skills: {skills}",
        ]
        if link:
            lines.append(f"   Apply: {link}")
        lines.append("")
    lines.append("— Job Scraper Enterprise")
    return "\n".join(lines)


# ── Transport functions ────────────────────────────────────────────────────────

async def _send_telegram(message: str) -> bool:
    """
    POST the digest message to the Telegram sendMessage API.

    Returns True on success, False on any error.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"Telegram digest sent (HTTP {resp.status_code})")
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(f"Telegram API error: {exc.response.status_code} — {exc.response.text[:200]}")
    except Exception as exc:
        logger.error(f"Telegram send failed: {exc}")
    return False


def _send_email(subject: str, body: str) -> bool:
    """
    Send the digest via SMTP (TLS on port 587).

    Returns True on success, False on any error.
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_TO]):
        logger.warning("SMTP not fully configured — skipping email fallback")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = SMTP_TO
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, SMTP_TO, msg.as_string())
        logger.info(f"Email digest sent to {SMTP_TO}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check SMTP_USER/SMTP_PASSWORD")
    except smtplib.SMTPException as exc:
        logger.error(f"SMTP error: {exc}")
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
    return False


# ── Public API ─────────────────────────────────────────────────────────────────

async def send_daily_digest(
    valid_jobs: List[Dict[str, Any]],
    run_id: Optional[int] = None,
    dry_run: bool = False,
) -> None:
    """
    Filter valid_jobs to those above DIGEST_SCORE_THRESHOLD, sort by score,
    take top DIGEST_TOP_N, and dispatch via Telegram (or email fallback).

    Parameters
    ----------
    valid_jobs:
        Full list of scored job dicts from the ingestion run.
    run_id:
        DB ScrapeRun ID for reference in the message.
    dry_run:
        If True, format the message and log it but do not send.
    """
    # Filter and rank
    qualifying = sorted(
        [j for j in valid_jobs if j.get("match_score", 0) >= DIGEST_SCORE_THRESHOLD],
        key=lambda j: j.get("match_score", 0),
        reverse=True,
    )[:DIGEST_TOP_N]

    if not qualifying:
        logger.info(f"Digest: no jobs met threshold ({DIGEST_SCORE_THRESHOLD}) — nothing to send")
        return

    logger.info(f"Digest: sending {len(qualifying)} qualifying leads (threshold={DIGEST_SCORE_THRESHOLD})")

    tg_message = _build_telegram_message(qualifying, run_id)
    email_body = _build_email_body(qualifying, run_id)
    email_subject = f"[Job Scraper] {len(qualifying)} high-match leads today"

    if dry_run:
        print("\n" + "=" * 60)
        print("[DRY RUN] Telegram message:")
        print("=" * 60)
        print(tg_message)
        print("\n" + "=" * 60)
        print("[DRY RUN] Email body:")
        print("=" * 60)
        print(email_body)
        return

    # Try Telegram first; email is the fallback
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        success = await _send_telegram(tg_message)
        if success:
            return

    # Fallback: email
    await asyncio.to_thread(_send_email, email_subject, email_body)


# ── CLI entry-point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daily digest notifier CLI")
    parser.add_argument("--dry-run", action="store_true", help="Print message without sending")
    args = parser.parse_args()

    # Synthesise a sample payload for CLI testing
    sample_jobs: List[Dict[str, Any]] = [
        {
            "title": "Senior Backend Engineer",
            "company": "Stripe",
            "match_score": 85,
            "top_jd_keywords": ["Python", "gRPC", "PostgreSQL", "Kubernetes"],
            "apply_link": "https://stripe.com/jobs/listing/1234",
        },
        {
            "title": "Platform Engineer",
            "company": "Razorpay",
            "match_score": 72,
            "top_jd_keywords": ["Go", "Kafka", "AWS", "Terraform"],
            "apply_link": "https://razorpay.com/jobs/5678",
        },
    ]

    asyncio.run(send_daily_digest(sample_jobs, run_id=99, dry_run=args.dry_run))
