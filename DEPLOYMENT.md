# VoiceScript Collector - Deployment Guide

## Quick Start with Docker Compose (Recommended)

### 1. Environment Setup
Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Generate a secure secret key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-generated-secret-key-here

# Database URL (auto-configured by docker-compose)
DATABASE_URL=postgresql://voicescript_user:voicescript_password@postgres:5432/voicescript_db

# Environment
FLASK_ENV=production
USE_HTTPS=false

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 2. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at `http://localhost:8000`

---

## Manual Docker Deployment

### 1. Build the Docker Image
```bash
docker build -t voicescript-collector .
```

### 2. Run with Environment File
```bash
# Using .env file (recommended)
docker run -d \
  --name voicescript \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  voicescript-collector
```

### 3. Run with Environment Variables (alternative)
```bash
docker run -d \
  --name voicescript \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e SECRET_KEY="your-secret-key" \
  -e FLASK_ENV="production" \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  voicescript-collector
```

---

## Database Migrations with Flask-Migrate

Flask-Migrate (Alembic) handles all database schema changes automatically.

### Common Commands

```bash
# View current migration status
flask db current

# View migration history
flask db history

# Generate new migration after model changes
flask db migrate -m "description of changes"

# Apply migrations
flask db upgrade

# Rollback one migration
flask db downgrade -1
```

### Adding New Features

1. **Update your models** in `app.py`
2. **Generate migration**: `flask db migrate -m "add new feature"`
3. **Review the generated migration** in `migrations/versions/`
4. **Apply migration**: `flask db upgrade`

Example workflow:
```bash
# After adding a new column to a model
flask db migrate -m "add email_verified column to users"
flask db upgrade
```

### In Production (Docker)

Migrations run automatically on container startup via `docker-entrypoint.sh`:
1. Checks if migrations directory exists
2. Detects schema changes
3. Applies pending migrations
4. Starts the application

---

## Database Connection Options

### Option 1: Managed PostgreSQL (Recommended)
Use services like:
- **Neon** (recommended): https://neon.tech
- **Supabase**: https://supabase.com
- **Railway**: https://railway.app
- **AWS RDS**
- **DigitalOcean Managed Databases**

```env
DATABASE_URL=postgresql://user:pass@host.region.neon.tech:5432/db?sslmode=require
```

### Option 2: Docker Compose with PostgreSQL
Already configured in `docker-compose.yml` - database runs in a container.

### Option 3: Local PostgreSQL
```bash
# Install PostgreSQL
sudo apt-get install postgresql

# Create database
sudo -u postgres createdb voicescript_db

# Create user
sudo -u postgres psql -c "CREATE USER voicescript WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE voicescript_db TO voicescript;"
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | Flask secret key for sessions |
| `FLASK_ENV` | No | `development` | Set to `production` for production |
| `USE_HTTPS` | No | `false` | Set to `true` if behind HTTPS proxy |
| `GOOGLE_CLIENT_ID` | No | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | - | Google OAuth secret |

---

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Generate strong SECRET_KEY**: `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Use HTTPS in production** (set `USE_HTTPS=true`)
4. **Use managed databases** with SSL/TLS enabled
5. **Keep dependencies updated**: `pip list --outdated`
6. **Review migration files** before applying to production

---

## Troubleshooting

### "Target database is not up to date"
```bash
flask db stamp head    # Sync database state
flask db migrate       # Generate new migration
flask db upgrade       # Apply it
```

### Reset Migrations (Development Only)
```bash
# WARNING: This will delete all migration history
rm -rf migrations/
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

### View Database Schema
```bash
# Connect to database
docker exec -it voicescript_postgres psql -U voicescript_user -d voicescript_db

# List tables
\dt

# Describe table
\d submissions

# Check migration version
SELECT * FROM alembic_version;
```

---

## Monitoring and Logs

### Docker Compose
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web

# View last 100 lines
docker-compose logs --tail=100 web
```

### Docker Container
```bash
# View logs
docker logs -f voicescript

# Access logs directory (mounted volume)
cat logs/app.log
```

---

## Backup and Restore

### PostgreSQL Backup
```bash
# Backup
docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db > backup.sql

# Restore
docker exec -i voicescript_postgres psql -U voicescript_user voicescript_db < backup.sql
```

### File Uploads Backup
```bash
# Backup uploads directory
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/

# Restore
tar -xzf uploads-backup-YYYYMMDD.tar.gz
```

---

## Need Help?

- Flask-Migrate Documentation: https://flask-migrate.readthedocs.io/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- Docker Documentation: https://docs.docker.com/
