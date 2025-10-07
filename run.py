#!/usr/bin/env python3
"""
Simple runner for the VoiceScript Collector Flask application
For local development only (not used by Docker)
"""

from app import app

if __name__ == '__main__':
    # Database initialization is automatic (handles both migrations and fallback)
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )