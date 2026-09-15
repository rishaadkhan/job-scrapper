# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install all Python dependencies into an isolated venv
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install OS-level build tools needed by lxml, bcrypt, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Create venv and install dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime — minimal image with only the venv and app code
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Create non-root user for least-privilege operation
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY . .

# Create data directory for SQLite DB + Excel outputs; adjust ownership
RUN mkdir -p /data/output && chown -R appuser:appuser /data /app

USER appuser

# Healthcheck — hits the FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Default: run the API server. Override with `python main.py` for the scheduler.
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
