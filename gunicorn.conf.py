# Gunicorn configuration file for production deployment
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "voicescript-collector"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
# Remove user/group settings for development environment compatibility
# user = "appuser"  # Only use in Docker with proper user setup
# group = "appuser"  # Only use in Docker with proper user setup
tmp_upload_dir = None

# SSL (if needed in production)
# keyfile = None
# certfile = None