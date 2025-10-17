# Use Python 3.11 slim image for better performance and security
FROM python:3.11-slim-bullseye

# Set metadata
LABEL maintainer="Kostiantyn Ivaschenko <kivaschenko@gmail.com>"
LABEL description="Laboratory Management System for Feed Plant Operations"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r laboratory && useradd -r -g laboratory laboratory

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY pyproject.toml README.md LICENSE ./
COPY laboratory/__init__.py laboratory/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[testing]"

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R laboratory:laboratory /app

# Switch to non-root user
USER laboratory

# Create volume for database
VOLUME ["/app/data"]

# Expose port
EXPOSE 6543

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6543/ || exit 1

# Default command
CMD ["pserve", "production.ini", "--reload"]
