#!/bin/bash

# Production startup script using Gunicorn
echo "🚀 Starting VoiceScript Collector in Production Mode"
echo "📊 Server will be available at: http://localhost:8000"
echo "👤 Demo Accounts: provider@demo.com, reviewer@demo.com, admin@demo.com (password: demo123)"
echo ""

# Set production environment
export FLASK_ENV=production

# Start Gunicorn with configuration
exec gunicorn --config gunicorn.conf.py app:app