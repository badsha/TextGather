#!/bin/bash
# Docker entrypoint script for VoiceScript Collector
# Database-First Migration System (Flyway-style)

set -e  # Exit on any error

export FLASK_APP=app:app

echo "============================================="
echo "VoiceScript Collector - Starting Deployment"
echo "============================================="

# Run database migrations using SQL scripts
echo ""
echo "Running database migrations..."
python db_migrator.py

if [ $? -eq 0 ]; then
    echo "✓ Database migration completed successfully"
else
    echo "✗ Database migration failed"
    exit 1
fi

# Start the application
echo ""
echo "Starting Gunicorn server..."
echo "============================================="
exec gunicorn --config gunicorn.conf.py app:app
