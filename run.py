#!/usr/bin/env python3
"""
Simple runner for the VoiceScript Collector Flask application
"""

from app import app

if __name__ == '__main__':
    # Database is automatically initialized when app module is imported
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )