#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    echo "Using DATABASE_URL from environment"
    alembic upgrade head
else
    echo "WARNING: DATABASE_URL not set, skipping migrations"
fi

# Start the application
echo "Starting application..."
exec "$@"
