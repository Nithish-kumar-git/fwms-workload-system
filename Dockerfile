# Multi-stage Dockerfile for Faculty Subject Selection System
# Python 3.12-slim base for minimal image size

# ============================================================================
# Stage 1: Builder (dependencies installation)
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime (minimal production image)
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY startup.sh ./startup.sh

# Make startup script executable
RUN chmod +x startup.sh

# Ensure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Set PYTHONPATH to ensure Python can find the app package
ENV PYTHONPATH=/app

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/health')" || exit 1

# Default command (can be overridden in docker-compose)
CMD ["sh", "startup.sh"]
