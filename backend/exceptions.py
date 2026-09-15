"""Typed custom exceptions and error models for structured error responses"""
from typing import Optional, Dict, Any
from datetime import datetime


class AppBaseException(Exception):
    """Base application exception with status code and error code"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NotFoundError(AppBaseException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, error_code="NOT_FOUND", details=details)


class AuthError(AppBaseException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_FAILED", details=details)


class ForbiddenError(AppBaseException):
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, error_code="FORBIDDEN", details=details)


class ValidationError(AppBaseException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details=details)


class ConflictError(AppBaseException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, error_code="CONFLICT", details=details)


class RateLimitError(AppBaseException):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", details=details)


class ScrapeError(AppBaseException):
    def __init__(self, message: str = "Scraping operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, error_code="SCRAPE_ERROR", details=details)


class ParseError(AppBaseException):
    def __init__(self, message: str = "Failed to parse target data", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, error_code="PARSE_ERROR", details=details)
