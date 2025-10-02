# Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- 2GB+ free disk space

### Standard Deployment (HTTP - Local Access)

1. **Clone/Download the repository**

2. **Build and start the containers:**
   ```bash
   docker-compose up -d
   ```

3. **Seed demo data:**
   ```bash
   docker exec -it voicescript_app flask seed-demo --force
   ```

4. **Access the application:**
   - Local: http://localhost:8000
   - Network: http://[YOUR_IP]:8000

### Demo Login
- Provider: http://localhost:8000/login?demo=provider
- Reviewer: http://localhost:8000/login?demo=reviewer
- Admin: http://localhost:8000/login?demo=admin

Or use the login form:
- Email: `provider@demo.com` / Password: `demo123`
- Email: `reviewer@demo.com` / Password: `demo123`
- Email: `admin@demo.com` / Password: `demo123`

## Environment Configuration

### Session Security (Important!)

The application uses different session configurations based on whether HTTPS is available:

**For HTTP deployments (Docker local):**
- Set `USE_HTTPS=false` (default)
- Sessions work over HTTP for local testing

**For HTTPS deployments (production with SSL):**
- Set `USE_HTTPS=true`
- Enables secure cookies (HTTPS only)

### Configuration Files

#### `.env.docker` - Default configuration
```env
DATABASE_URL=postgresql://voicescript_user:voicescript_password@postgres:5432/voicescript_db
FLASK_ENV=production
SECRET_KEY=production-secret-key-change-this-in-production
USE_HTTPS=false  # Set to true if using HTTPS/SSL
ENABLE_WEBVIEW_FALLBACK=false  # MUST be false in production for security
```

#### `docker-compose.yml` - Environment variables
```yaml
environment:
  - DATABASE_URL=postgresql://voicescript_user:voicescript_password@postgres:5432/voicescript_db
  - FLASK_ENV=production
  - SECRET_KEY=production-secret-key-change-this-in-production
  - USE_HTTPS=false  # Change to true for HTTPS
```

## Production HTTPS Setup

If deploying behind an HTTPS proxy (nginx, Traefik, etc.):

1. **Update environment variables:**
   ```yaml
   environment:
     - USE_HTTPS=true
     - SECRET_KEY=your-strong-secret-key-here
   ```

2. **Configure your reverse proxy to forward:**
   - `X-Forwarded-Proto: https`
   - `X-Forwarded-For: client_ip`

3. **Example nginx configuration:**
   ```nginx
   location / {
       proxy_pass http://localhost:8000;
       proxy_set_header X-Forwarded-Proto https;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header Host $host;
   }
   ```

## Database Management

### Seed Demo Data
```bash
# Seed demo data (13 users, 5 scripts, 10 languages)
docker exec -it voicescript_app flask seed-demo

# Force recreate demo data
docker exec -it voicescript_app flask seed-demo --force
```

### Database Backup
```bash
# Backup PostgreSQL database
docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db > backup.sql

# Restore backup
docker exec -i voicescript_postgres psql -U voicescript_user voicescript_db < backup.sql
```

### Access PostgreSQL CLI
```bash
docker exec -it voicescript_postgres psql -U voicescript_user -d voicescript_db
```

## Container Management

### View Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f web
docker-compose logs -f postgres
```

### Stop/Start
```bash
# Stop containers
docker-compose down

# Start containers
docker-compose up -d

# Rebuild after code changes
docker-compose up -d --build
```

### Clean Restart
```bash
# Remove containers and volumes (DELETES DATA!)
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build

# Seed demo data again
docker exec -it voicescript_app flask seed-demo --force
```

## Troubleshooting

### Login Redirects to Index Page

**Problem:** Demo login or regular login redirects back to index/login page instead of dashboard.

**Solution:** Ensure `USE_HTTPS=false` is set in your environment if accessing via HTTP:

```yaml
# docker-compose.yml
environment:
  - USE_HTTPS=false  # MUST be false for HTTP access
```

**Why this happens:** 
- When `USE_HTTPS=true`, the app sets secure cookies requiring HTTPS
- Accessing via HTTP (http://localhost:8000) won't send secure cookies
- Session fails, causing login redirects

### Microphone Not Working

**Problem:** Audio recording doesn't work in browser.

**Solution:** Use `https://` or `localhost` for microphone access:
- ✅ Works: `https://yourdomain.com` or `http://localhost:8000`
- ❌ Fails: `http://192.168.1.100:8000` (use HTTPS for network access)

### Container Health Checks Failing

```bash
# Check container status
docker-compose ps

# View detailed health logs
docker inspect voicescript_app | grep -A 20 Health
```

### Database Connection Issues

```bash
# Check if PostgreSQL is ready
docker exec voicescript_postgres pg_isready -U voicescript_user

# Verify connection from app container
docker exec voicescript_app flask db-check
```

### Port Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "9000:8000"  # Access via localhost:9000
```

## File Persistence

Docker volumes persist data between container restarts:

```yaml
volumes:
  - ./uploads:/app/uploads    # Audio files
  - ./logs:/app/logs          # Application logs
  - postgres_data:/var/lib/postgresql/data  # Database
```

To completely reset:
```bash
docker-compose down -v  # Removes volumes
rm -rf uploads/ logs/   # Removes local files
```

## Security Best Practices

1. **Change default secrets:**
   - Generate strong `SECRET_KEY`: `openssl rand -hex 32`
   - Update PostgreSQL password in both `.env.docker` and `docker-compose.yml`

2. **Use HTTPS in production:**
   - Set `USE_HTTPS=true`
   - Configure SSL termination with nginx/Traefik

3. **Restrict database access:**
   - Don't expose PostgreSQL port publicly
   - Use firewall rules to limit access

4. **Regular backups:**
   - Schedule automated database backups
   - Store backups securely off-server

## Network Configuration

### Access from Other Devices

The app is accessible on your local network:

1. Find your machine's IP:
   ```bash
   # Linux/macOS
   ip addr show | grep inet
   
   # Windows
   ipconfig
   ```

2. Access from other devices:
   ```
   http://[YOUR_IP]:8000
   ```

**Note:** Microphone access requires HTTPS or localhost. Use HTTPS for network access.

## Performance Tuning

### Gunicorn Workers
Adjust worker count in `gunicorn.conf.py`:
```python
workers = 4  # Recommended: (2 x CPU cores) + 1
```

### PostgreSQL Connection Pool
Adjust in `app.py`:
```python
'pool_size': 10,      # Increase for high traffic
'max_overflow': 20,   # Additional connections
```

### Resource Limits
Add to `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

## Monitoring

### Health Endpoints
```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/db-health
```

### Container Stats
```bash
docker stats voicescript_app voicescript_postgres
```

## Upgrading

1. **Backup data:**
   ```bash
   docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db > backup.sql
   ```

2. **Pull latest changes:**
   ```bash
   git pull  # or download latest release
   ```

3. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

4. **Verify:**
   ```bash
   docker-compose logs -f
   ```

## Support

For issues:
1. Check container logs: `docker-compose logs -f`
2. Verify environment variables: `docker exec voicescript_app env`
3. Test database connection: `docker exec voicescript_app flask db-check`
4. Review this guide for common issues
