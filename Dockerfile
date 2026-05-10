# Stage 1: build React frontend
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
RUN cd frontend && npm run build
# outDir is ../commerce_platform/web/static → /app/commerce_platform/web/static

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY commerce_platform/ ./commerce_platform/
COPY config.yaml ./

# Overlay compiled frontend
COPY --from=frontend /app/commerce_platform/web/static/ ./commerce_platform/web/static/

EXPOSE 8000
CMD ["python", "-m", "commerce_platform", "--host", "0.0.0.0", "--port", "8000"]
