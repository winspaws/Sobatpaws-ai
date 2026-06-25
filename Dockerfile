# =============================================================================
#  Ekosistem Satwa — Production Dockerfile (multi-stage, slim image)
#  Target: Python 3.11 runtime with ML dependencies (scikit-learn, pandas)
#  Build:  docker build -t ekosistemsatwa-api:latest .
# =============================================================================

# ── Stage 1: Builder ──────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

LABEL stage=builder

# Install build dependencies (scikit-learn needs wheel/numpy build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="Naincode AI Dept"
LABEL description="Ekosistem Satwa — Veterinary Backend AI Services (rebranded from Sobatpaws)"
LABEL version="0.3.0"

# Runtime dependencies (no build tools needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with uid 1000 (matches VPS ubuntu user for volume permissions)
RUN groupadd -r ekosistemsatwa -g 1000 && useradd -r -g ekosistemsatwa -u 1000 -d /app -s /sbin/nologin ekosistemsatwa

WORKDIR /app

# Copy installed Python packages from builder
# Copy installed Python packages to system-wide location
COPY --from=builder /root/.local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /root/.local/bin /usr/local/bin

# Copy application source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY web/ ./web/
COPY data/ ./data/
COPY dbml/ ./dbml/
COPY requirements.txt .

# Create writable directories for runtime artifacts and fix permissions
RUN mkdir -p /app/artifacts/models /app/artifacts/learning /app/artifacts/ai /app/artifacts/sessions \
    && chown -R ekosistemsatwa:ekosistemsatwa /app

# PYTHONPATH for imports
ENV PYTHONPATH=/app/src

# ── Health check ──────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# ── Run ───────────────────────────────────────────────────────────────────
USER ekosistemsatwa
EXPOSE 8000

CMD ["uvicorn", "ekosistem_satwa.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
