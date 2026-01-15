FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r nova && useradd -r -g nova nova

# Copy application code
COPY app /app/app

# Copy tests (for integration testing)
COPY tests /app/tests

# Copy alembic migrations
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Copy scripts
COPY scripts /app/scripts

# Change ownership to non-root user
RUN chown -R nova:nova /app

# Switch to non-root user
USER nova

EXPOSE 8000

# Use shell form to allow env var substitution for HOST binding
# Note: Using 2 workers to prevent CPU starvation from concurrent requests (health checks, OpenAPI, etc.)
CMD uvicorn app.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --proxy-headers --workers 2
