# Dedicated demo only: build context is the repository root.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY demo/start_backend.py demo/healthcheck.py ./demo/
RUN useradd --system --uid 10001 demoapp && mkdir -p /app/logs && chown demoapp /app/logs
USER demoapp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python", "demo/healthcheck.py"]
CMD ["python", "demo/start_backend.py"]
