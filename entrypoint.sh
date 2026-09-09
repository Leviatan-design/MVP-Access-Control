#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    echo "Using DATABASE_URL from environment"
    alembic upgrade head
else
    echo "ERROR: DATABASE_URL is required and must point to PostgreSQL"
    exit 1
fi

# Start the application
echo "Starting application..."
exec "$@"
