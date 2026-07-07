# Hermes Autonomous Multi-Agent System - Docker Image

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Hermes agent source (assumes hermes-agent is in parent directory)
# If deploying, you may need to:
# 1. Copy from ~/.hermes/hermes-agent
# 2. Or install from git: pip install git+https://github.com/NousResearch/hermes-agent.git
COPY hermes-agent/ /opt/hermes-agent/
WORKDIR /opt/hermes-agent
RUN pip install --no-cache-dir -e .

# Back to app directory
WORKDIR /app

# Copy application code
COPY autonomous/ ./autonomous/
COPY agents/ ./agents/
COPY skills/ ./skills/
COPY cron_config.yaml .

# Create log directory
RUN mkdir -p /var/log/hermes

# Environment variables (will be overridden by Railway)
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=""
ENV REDIS_URL=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_WEBHOOK_URL=""
ENV ANTHROPIC_API_KEY=""
ENV OPENAI_API_KEY=""

# Expose port for webhook (Railway will assign PORT)
EXPOSE ${PORT:-8080}

# Health check endpoint
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Copy main application
COPY main.py .

# Start script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh /app/main.py

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: Run main application (Telegram bot + scheduler)
CMD ["python", "main.py"]
