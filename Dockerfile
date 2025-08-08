# Multi-stage build for optimized production image
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim as builder

# Set build environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with version pinning
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:${PYTHON_VERSION}-slim

# Add labels for container management
LABEL maintainer="your-email@example.com" \
      version="1.0.0" \
      description="FastAPI ZK Audit System Backend"

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FASTAPI_ENV=production \
    LOG_LEVEL=info \
    WORKERS=4 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Create app user and group with specific IDs for security
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -d /app -s /bin/bash appuser

# Install runtime dependencies only with version pinning
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory and set working directory
WORKDIR /app

# Copy application files with proper ownership
COPY --chown=appuser:appuser \
    fastapi-server.py \
    cloud_data_ingestion.py \
    random_block_selector.py \
    create_sample_dataset.py \
    ./

# Create necessary directories with specific permissions
RUN mkdir -p upload_blocks merkle_commitments test_blocks_commitments logs && \
    chmod 750 upload_blocks merkle_commitments test_blocks_commitments && \
    chmod 755 logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Enhanced health check with better configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Start the application with production configuration
CMD ["python", "-m", "uvicorn", "fastapi-server:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]