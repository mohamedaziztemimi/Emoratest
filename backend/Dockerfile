# ────────────────────────────────────────────────────────────────
# Backend Dockerfile - EmoraTest FastAPI Application
# ────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY pyproject.toml .

# Install Python dependencies (without dev extras for production)
RUN pip install --no-cache-dir -e "."

# Copy application code
COPY . .

EXPOSE 8000

# Development mode: hot-reload enabled via uvicorn --reload
# Production mode: override CMD without --reload flag
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
