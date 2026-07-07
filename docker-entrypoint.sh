#!/bin/bash
set -e

echo "=================================="
echo "Hermes Autonomous Multi-Agent System"
echo "=================================="

# Wait for PostgreSQL to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL..."
    until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
        echo "PostgreSQL not ready, waiting..."
        sleep 2
    done
    echo "PostgreSQL is ready!"
fi

# Wait for Redis to be ready
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    until python -c "import redis; redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
        echo "Redis not ready, waiting..."
        sleep 2
    done
    echo "Redis is ready!"
fi

# Initialize database schema
echo "Initializing database schema..."
python -c "
from autonomous.knowledge_base import KnowledgeBase
kb = KnowledgeBase()
print('Database schema initialized successfully!')
kb.close()
" || echo "Schema already exists or initialization failed (continuing anyway)"

# Display configuration
echo "=================================="
echo "Configuration:"
echo "  Database: ${DATABASE_URL:0:30}..."
echo "  Redis: ${REDIS_URL:0:30}..."
echo "  Telegram Bot: ${TELEGRAM_BOT_TOKEN:+configured}"
echo "  Webhook URL: ${TELEGRAM_WEBHOOK_URL:-not set}"
echo "=================================="

# Execute the main command
echo "Starting application..."
exec "$@"
