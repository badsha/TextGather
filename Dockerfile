# ---- Stage 1: Builder ----
# This stage installs dependencies into a virtual environment.
FROM python:3.11-slim as builder

WORKDIR /app

# Create a non-root user for security purposes
RUN useradd --create-home --shell /bin/bash appuser

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the requirements file first to leverage Docker's layer caching.
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Final Image ----
# This stage creates the final, lean image for running the application.
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Use the same non-root user as in the builder stage
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment with installed packages from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application source code. .dockerignore will prevent .env and other files from being copied.
COPY . .

# Grant ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Set the PATH environment variable to include the venv
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port your application runs on (updated for Docker setup)
EXPOSE 8000

# Use Gunicorn as the production WSGI server instead of Flask dev server
# The entrypoint script runs database migrations before starting the server
# Configuration is in gunicorn.conf.py:
# --bind 0.0.0.0:8000: Listen on all interfaces on port 8000
# --workers 4: Use 4 worker processes for better performance
# --timeout 120: Set request timeout to 2 minutes
# --access-logfile -: Log access to stdout
# --error-logfile -: Log errors to stderr
ENTRYPOINT ["/app/docker-entrypoint.sh"]