"""Cloudflare R2 (S3-compatible) Object Storage client for compiled PDF resumes"""
import os
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger("jobscraper.storage.r2")


def _get_r2_credentials():
    """Retrieve and validate Cloudflare R2 credentials from settings or environment."""
    cfg = settings
    access_key = cfg.R2_ACCESS_KEY if cfg else os.getenv("R2_ACCESS_KEY", "")
    secret_key = cfg.R2_SECRET_KEY if cfg else os.getenv("R2_SECRET_KEY", "")
    bucket = cfg.R2_BUCKET if cfg else os.getenv("R2_BUCKET", "")
    endpoint = cfg.R2_ENDPOINT if cfg else os.getenv("R2_ENDPOINT", "")
    public_url = cfg.R2_PUBLIC_URL if cfg else os.getenv("R2_PUBLIC_URL", "")

    if not all([access_key, secret_key, bucket, endpoint]):
        return None

    return {
        "access_key": access_key.strip(),
        "secret_key": secret_key.strip(),
        "bucket": bucket.strip(),
        "endpoint": endpoint.strip(),
        "public_url": public_url.strip() if public_url else ""
    }


def upload_pdf(pdf_bytes: bytes, key: str, s3_client=None) -> Optional[str]:
    """
    Upload compiled PDF bytes to Cloudflare R2 object storage.
    
    If R2 credentials are unset or incomplete:
    - Logs a clear warning
    - Storing PDFs is disabled
    - Returns None cleanly without raising
    
    Returns:
        Public download URL or S3 object URL if successful, None otherwise.
    """
    creds = _get_r2_credentials()
    if not creds and not s3_client:
        logger.warning(
            "Cloudflare R2 configuration incomplete (R2_ACCESS_KEY, R2_SECRET_KEY, "
            "R2_BUCKET, R2_ENDPOINT). PDF object storage is DISABLED."
        )
        return None

    clean_key = key.lstrip("/")

    try:
        if s3_client is None:
            import boto3
            from botocore.config import Config
            s3_client = boto3.client(
                "s3",
                endpoint_url=creds["endpoint"],
                aws_access_key_id=creds["access_key"],
                aws_secret_access_key=creds["secret_key"],
                config=Config(signature_version="s3v4")
            )

        bucket_name = creds["bucket"] if creds else "test-bucket"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=clean_key,
            Body=pdf_bytes,
            ContentType="application/pdf"
        )

        if creds and creds["public_url"]:
            url = f"{creds['public_url'].rstrip('/')}/{clean_key}"
        elif creds:
            url = f"{creds['endpoint'].rstrip('/')}/{bucket_name}/{clean_key}"
        else:
            url = f"https://r2.cloudflarestorage.com/{bucket_name}/{clean_key}"

        logger.info(f"Successfully uploaded PDF to Cloudflare R2: key='{clean_key}', url='{url}'")
        return url

    except Exception as exc:
        logger.error(f"Failed to upload PDF to R2 (key='{clean_key}'): {exc}")
        return None


def delete_pdf(key: str, s3_client=None) -> bool:
    """
    Delete a PDF object from Cloudflare R2 object storage by key.
    
    If R2 credentials are unset:
    - Logs a warning
    - Returns False cleanly without raising
    
    Returns:
        True if successfully deleted, False otherwise.
    """
    creds = _get_r2_credentials()
    if not creds and not s3_client:
        logger.warning("Cloudflare R2 credentials unset. Skipping PDF deletion.")
        return False

    clean_key = key.lstrip("/")

    try:
        if s3_client is None:
            import boto3
            from botocore.config import Config
            s3_client = boto3.client(
                "s3",
                endpoint_url=creds["endpoint"],
                aws_access_key_id=creds["access_key"],
                aws_secret_access_key=creds["secret_key"],
                config=Config(signature_version="s3v4")
            )

        bucket_name = creds["bucket"] if creds else "test-bucket"

        s3_client.delete_object(
            Bucket=bucket_name,
            Key=clean_key
        )
        logger.info(f"Successfully deleted PDF from Cloudflare R2: key='{clean_key}'")
        return True

    except Exception as exc:
        logger.error(f"Failed to delete PDF from R2 (key='{clean_key}'): {exc}")
        return False
