# ─────────────────────────────────────────────────────────────────────────────
# Sandboxed LaTeX Compiler Microservice (Tectonic Engine)
# Hardened, lightweight compilation container running as non-root user.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Install system utilities & required libraries for Tectonic typesetting
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fontconfig \
    libharfbuzz0b \
    libicu72 \
    libgraphite2-3 \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic pre-compiled static binary
ARG TECTONIC_VERSION=0.15.0
RUN curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    | tar -xz -C /usr/local/bin && \
    chmod +x /usr/local/bin/tectonic

# Create dedicated non-root user and group
RUN groupadd -g 1001 compiler && \
    useradd -u 1001 -g compiler -m -s /bin/bash compiler

WORKDIR /app

# Configure bundle cache directory for non-root user
ENV TECTONIC_CACHE_DIR=/home/compiler/.cache/Tectonic
ENV XDG_CACHE_HOME=/home/compiler/.cache
ENV TECTONIC_UNTRUSTED_MODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /home/compiler/.cache/Tectonic && \
    chown -R compiler:compiler /home/compiler

# Install Python microservice dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY . .
RUN chown -R compiler:compiler /app

# Switch to non-root user
USER compiler

# Pre-warm tectonic default bundle cache during build so offline compilation succeeds
RUN mkdir -p /tmp/prewarm && \
    printf '\\documentclass{article}\\begin{document}Prewarm\\end{document}\n' > /tmp/prewarm/doc.tex && \
    (tectonic -o /tmp/prewarm /tmp/prewarm/doc.tex || true) && \
    rm -rf /tmp/prewarm

# Expose internal microservice port (only accessible inside internal container network)
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
