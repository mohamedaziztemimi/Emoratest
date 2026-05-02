# ────────────────────────────────────────────────────────────────
# Backend Dockerfile - EmoraTest FastAPI Application
# ────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Copy dependency file
COPY pyproject.toml .

# Install Python dependencies (without dev extras for production)
RUN pip install --no-cache-dir -e "."

# Copy application code
COPY . .

# Copy ML model artifacts
COPY ml/artifacts /app/ml_artifacts

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Development mode: hot-reload enabled via uvicorn --reload
# Production mode: override CMD without --reload flag
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
