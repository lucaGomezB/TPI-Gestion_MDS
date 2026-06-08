# =============================================================================
# Stage 1 — Builder: install dependencies into a virtual environment
# =============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build

# Install system build deps (only needed during pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2 — Runtime: minimal image with only the venv + app code
# =============================================================================
FROM python:3.13-slim AS runtime

# Create a non-root user for security
RUN groupadd --system --gid 1001 app && \
    useradd --system --gid app --uid 1001 --no-create-home app

WORKDIR /app

# Copy the venv from builder — this is the ONLY Python we need
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy application source code
COPY app/ app/
COPY run_worker.py .

# Switch to non-root user
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health', timeout=5)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
