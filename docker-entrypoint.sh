#!/bin/bash
# Docker entrypoint script for VoiceScript Collector
# This script initializes database and runs migrations

set -e  # Exit on any error

# Set Flask app for Flask-Migrate commands
export FLASK_APP=app:app

echo "============================================="
echo "VoiceScript Collector - Starting Deployment"
echo "============================================="

# Step 1: Initialize migrations directory if it doesn't exist
echo ""
echo "Step 1: Checking migrations setup..."
if [ ! -d "migrations" ]; then
    echo "Initializing Flask-Migrate..."
    flask db init
fi

# Step 2: Check if this is a fresh database or existing one
echo ""
echo "Step 2: Checking database state..."
DB_HAS_TABLES=$(python -c "
from app import app, db
from sqlalchemy import inspect
app.app_context().push()
inspector = inspect(db.engine)
tables = inspector.get_table_names()
print('yes' if len(tables) > 0 else 'no')
" 2>/dev/null || echo "no")

if [ "$DB_HAS_TABLES" = "no" ]; then
    echo "Fresh database detected - creating schema..."
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✓ Database schema created')"
    
    # Stamp the base migration for fresh databases
    echo "Stamping base migration..."
    flask db stamp 001_initial_schema
else
    echo "Existing database detected - checking migration status..."
    
    # Check if alembic_version table exists
    HAS_ALEMBIC=$(python -c "
from app import app, db
from sqlalchemy import inspect
app.app_context().push()
inspector = inspect(db.engine)
tables = inspector.get_table_names()
print('yes' if 'alembic_version' in tables else 'no')
" 2>/dev/null || echo "no")
    
    if [ "$HAS_ALEMBIC" = "no" ]; then
        echo "First-time migration setup for existing database..."
        echo "Stamping base migration as complete..."
        flask db stamp 001_initial_schema
    else
        echo "Migration system already initialized"
    fi
fi

# Step 3: Run any pending migrations
echo ""
echo "Step 3: Running pending migrations..."
flask db upgrade

if [ $? -eq 0 ]; then
    echo "✓ All migrations completed successfully"
else
    echo "✗ Migrations failed"
    exit 1
fi

# Step 4: Start the application
echo ""
echo "Step 4: Starting Gunicorn server..."
echo "============================================="
exec gunicorn --config gunicorn.conf.py app:app
