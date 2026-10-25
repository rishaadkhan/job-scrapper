"""Object storage client package"""
from storage.r2_client import upload_pdf, delete_pdf

__all__ = ["upload_pdf", "delete_pdf"]
