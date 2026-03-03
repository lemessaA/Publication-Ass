# Multi-stage build for Production: backend + frontend in one image
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend static assets to be served by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./static

# Copy app code
COPY app/ ./app/

# Non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
RUN pip install --no-cache-dir httpx
COPY <<'EOF' /app/healthcheck.py
import httpx, sys, os
port = int(os.getenv("PORT", 8000))
try:
    r = httpx.get(f"http://localhost:{port}/healthz", timeout=5)
    sys.exit(0 if r.status_code == 200 else 1)
except Exception:
    sys.exit(1)
EOF

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

EXPOSE 8000

# Use env var for port (default 8000)
ENV PORT=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
