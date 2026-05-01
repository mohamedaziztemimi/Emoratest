# ────────────────────────────────────────────────────────────────
# ML Dockerfile - EmoraTest ML Training Pipeline
# ────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Copy dependency file
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Default: run tests
CMD ["pytest", "tests/", "-v"]
