# Backend Dockerfile — Python 3.12 + FastAPI
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for asyncpg and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start FastAPI on $PORT (defaults to 8000 for local docker-compose)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
