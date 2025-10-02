# Docker Login Fix - Update Instructions

## What Was Fixed

Your Docker deployment had a session configuration issue causing login redirects. This has been **completely fixed** with two important changes:

### 1. Session Cookie Configuration (Login Fix)
- **Problem**: Secure cookies required HTTPS, but Docker runs on HTTP
- **Solution**: Added `USE_HTTPS=false` environment variable
- **Result**: Sessions now work correctly on HTTP (localhost:8000)

### 2. Security Hardening (Critical)
- **Problem**: Fallback authentication allowed privilege escalation via forged cookies
- **Solution**: Added `ENABLE_WEBVIEW_FALLBACK=false` to disable insecure fallback auth
- **Result**: Production deployments are now secure

## How to Update Your Docker Deployment

### Option 1: Pull Latest Changes (Recommended)

```bash
# Stop containers
docker-compose down

# Pull latest code
git pull  # or re-download the latest version

# Rebuild and start
docker-compose up -d --build

# Seed demo data
docker exec -it voicescript_app flask seed-demo --force
```

### Option 2: Manual Configuration Update

If you can't pull new code, manually update these files:

#### 1. Update `docker-compose.yml`
Add these two environment variables:

```yaml
environment:
  - DATABASE_URL=postgresql://voicescript_user:voicescript_password@postgres:5432/voicescript_db
  - FLASK_ENV=production
  - SECRET_KEY=production-secret-key-change-this-in-production
  - USE_HTTPS=false           # ADD THIS LINE
  - ENABLE_WEBVIEW_FALLBACK=false  # ADD THIS LINE
```

#### 2. Update `.env.docker`
Add these two lines:

```env
USE_HTTPS=false
ENABLE_WEBVIEW_FALLBACK=false
```

#### 3. Rebuild and Restart

```bash
docker-compose down
docker-compose up -d --build
```

## Verify It's Working

### Test Demo Login
Visit these URLs to test each role:
- Provider: http://localhost:8000/login?demo=provider
- Reviewer: http://localhost:8000/login?demo=reviewer
- Admin: http://localhost:8000/login?demo=admin

**Expected Result**: You should be taken directly to the appropriate dashboard (no redirect loop)

### Test Regular Login
1. Go to: http://localhost:8000
2. Click "Login"
3. Enter: `provider@demo.com` / `demo123`
4. **Expected Result**: Redirected to Provider Dashboard

## Important Configuration Notes

### USE_HTTPS Flag
- **For HTTP (local Docker)**: `USE_HTTPS=false` (default)
- **For HTTPS (production with SSL)**: `USE_HTTPS=true`

### ENABLE_WEBVIEW_FALLBACK Flag
- **Must be `false` in production** (security requirement)
- **Only set to `true` in development** if using Replit webview

## Production HTTPS Setup

If deploying with HTTPS (nginx, Traefik, etc.):

1. **Set environment variables:**
   ```yaml
   environment:
     - USE_HTTPS=true
     - ENABLE_WEBVIEW_FALLBACK=false
     - SECRET_KEY=your-strong-secret-key
   ```

2. **Configure reverse proxy:**
   ```nginx
   location / {
       proxy_pass http://localhost:8000;
       proxy_set_header X-Forwarded-Proto https;
       proxy_set_header Host $host;
   }
   ```

## Security Best Practices

1. ✅ Always keep `ENABLE_WEBVIEW_FALLBACK=false` in production
2. ✅ Use `USE_HTTPS=true` only when actually running on HTTPS
3. ✅ Change `SECRET_KEY` to a strong random value
4. ✅ Update PostgreSQL password in production

## Troubleshooting

### Still Getting Login Redirects?

1. **Verify environment variables:**
   ```bash
   docker exec voicescript_app env | grep -E "(USE_HTTPS|ENABLE_WEBVIEW_FALLBACK)"
   ```
   Should show:
   ```
   USE_HTTPS=false
   ENABLE_WEBVIEW_FALLBACK=false
   ```

2. **Check container logs:**
   ```bash
   docker-compose logs -f web
   ```

3. **Rebuild from scratch:**
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   docker exec -it voicescript_app flask seed-demo --force
   ```

### Microphone Not Working?

Use `https://` or `localhost` for microphone access:
- ✅ Works: `http://localhost:8000`
- ❌ Fails: `http://192.168.1.100:8000` (use HTTPS for network access)

## Complete Documentation

For comprehensive Docker deployment guide, see:
- **DOCKER.md** - Full Docker deployment and troubleshooting guide
- **README.md** - General application documentation
- **replit.md** - Technical architecture and recent changes

## Questions?

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Review DOCKER.md for detailed troubleshooting
3. Verify environment variables are set correctly
4. Ensure you're using the latest version of the code
