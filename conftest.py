"""
Pytest root configuration and fixtures.
Ensures repository root is in sys.path and provides clean environment defaults for tests.
"""
import sys
import os
from pathlib import Path

# Ensure repo root is explicitly at the head of sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Provide safe fallback test environment variables if not set
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///jobscraper.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-collection")
os.environ.setdefault("ADMIN_EMAIL", "test@jobscraper.local")
os.environ.setdefault("ADMIN_PASSWORD", "testpass123")
