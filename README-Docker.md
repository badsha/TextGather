# VoiceScript Collector - Docker PostgreSQL Setup

## Overview

Your VoiceScript Collector application has been fully dockerized with PostgreSQL database support. The setup includes:

- **PostgreSQL 15** database container
- **Flask application** container with Gunicorn
- **Docker Compose** orchestration
- **Health checks** for both services
- **Production-ready** configuration

## Quick Start

1. **Clone/Download** your codebase to a local machine with Docker installed

2. **Build and run** the containers:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Application: http://localhost:8000
   - Health Check: http://localhost:8000/health

## Configuration Files Created

### 1. `docker-compose.yml`
- PostgreSQL service with persistent volume
- Flask application service
- Network configuration
- Health checks for both services
- Environment variable management

### 2. Updated `Dockerfile`
- Multi-stage build for optimization
- PostgreSQL client libraries
- Production Gunicorn configuration
- Port 8000 exposure
- Security best practices (non-root user)

### 3. `gunicorn.conf.py` (Updated)
- Bind to 0.0.0.0:8000
- 4 worker processes
- Request timeout: 120 seconds
- Production logging

### 4. `.env.docker` (Template)
- PostgreSQL connection settings
- Flask production configuration
- Google OAuth placeholders

### 5. Health Check Endpoint
- `/health` endpoint added to Flask app
- Tests database connectivity
- Used by Docker health checks

## Database Configuration

The application now uses PostgreSQL by default when running in Docker:

```
DATABASE_URL=postgresql://voicescript_user:voicescript_password@postgres:5432/voicescript_db
```

### Database Features:
- **Persistent storage** with Docker volumes
- **Connection pooling** for stability
- **Health monitoring** with automatic retries
- **Automatic schema migration** on startup

## Environment Variables

### Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Flask secret key for sessions

### Optional:
- `GOOGLE_CLIENT_ID` - For Google OAuth
- `GOOGLE_CLIENT_SECRET` - For Google OAuth
- `FLASK_ENV` - Set to 'production' for Docker

## Services

### PostgreSQL Service (`postgres`)
- **Image**: postgres:15-alpine
- **Database**: voicescript_db
- **User**: voicescript_user
- **Password**: voicescript_password
- **Port**: 5432 (mapped to host)
- **Volume**: postgres_data (persistent)

### Web Service (`web`)
- **Build**: From local Dockerfile
- **Port**: 8000 (mapped to host)
- **Depends on**: PostgreSQL service
- **Restart**: unless-stopped
- **User**: appuser (non-root)

## Commands

### Start services:
```bash
docker-compose up
```

### Start in background:
```bash
docker-compose up -d
```

### Rebuild and start:
```bash
docker-compose up --build
```

### Stop services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs web
docker-compose logs postgres
```

### Access database:
```bash
docker-compose exec postgres psql -U voicescript_user -d voicescript_db
```

## Production Deployment

For production deployment:

1. **Update environment variables** in `.env.docker`
2. **Change default passwords** for security
3. **Configure SSL/TLS** if needed
4. **Set up backup strategy** for PostgreSQL data
5. **Configure reverse proxy** (nginx/Apache) if needed

## Data Migration from SQLite

If you have existing SQLite data to migrate:

1. **Export data** from SQLite using Python scripts
2. **Import data** to PostgreSQL using the Flask shell
3. **Or use migration tools** like pgloader

## Troubleshooting

### Database Connection Issues:
- Check if PostgreSQL container is healthy: `docker-compose ps`
- View PostgreSQL logs: `docker-compose logs postgres`
- Verify environment variables are set correctly

### Application Issues:
- Check application logs: `docker-compose logs web`
- Verify health endpoint: `curl http://localhost:8000/health`
- Ensure port 8000 is not in use by other services

### Performance:
- Adjust Gunicorn workers in `gunicorn.conf.py`
- Monitor resource usage: `docker stats`
- Scale services if needed: `docker-compose up --scale web=3`

## Development vs Production

- **Development**: Run `python run.py` locally with SQLite
- **Production**: Use Docker Compose with PostgreSQL
- **Testing**: Run containers locally before deployment

Your application is now fully dockerized and PostgreSQL-ready! 🐳