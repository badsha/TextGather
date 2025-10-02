# VoiceScript Collector - Installation Guide

## 📋 Prerequisites

Before you begin, ensure you have:

- **Server with public IP** (Ubuntu 20.04+ or similar Linux distribution)
- **Docker** and **Docker Compose** installed
- **Domain name** pointing to your server's public IP (e.g., from DuckDNS, Freenom, or any registrar)
- **Ports 80 and 443** accessible from the internet
- **Root/sudo access** for firewall configuration

---

## 🚀 Quick Start (Automated Setup)

### Step 1: Download the Codebase

```bash
# Clone or download the repository
cd /path/to/voicescript-collector
```

### Step 2: Clean Any Previous Installation

```bash
# Stop any running containers
docker-compose down
docker-compose -f docker-compose-secure.yml down

# Remove old database volume (if exists)
docker volume rm voicescript_postgres_data 2>/dev/null || true

# Clean up old certificates
rm -rf certbot/conf/* certbot/www/*
```

### Step 3: Make Setup Script Executable

```bash
chmod +x setup-https.sh
```

### Step 4: Run Automated HTTPS Setup

```bash
sudo ./setup-https.sh
```

When prompted, enter:
- **Your domain name** (e.g., `textgather.duckdns.org`)
- **Your email address** (for SSL certificate notifications)

The script will automatically:
1. ✅ Generate secure SECRET_KEY and database password
2. ✅ Create `.env` file with production settings
3. ✅ Configure nginx for your domain
4. ✅ Set up firewall rules (allow 22, 80, 443; block 8000, 5432)
5. ✅ Obtain Let's Encrypt SSL certificate
6. ✅ Start all services securely
7. ✅ Seed demo data

### Step 5: Access Your Application

Visit: `https://your-domain.com`

**Demo Accounts:**
- Provider: `https://your-domain.com/login?demo=provider`
- Reviewer: `https://your-domain.com/login?demo=reviewer`
- Admin: `https://your-domain.com/login?demo=admin`

**All demo accounts use password:** `demo123`

---

## 🔧 Manual Installation (Step-by-Step)

If you prefer manual setup or the automated script fails:

### Step 1: Clean Installation

```bash
# Stop all containers
docker-compose down
docker-compose -f docker-compose-secure.yml down

# Remove old volumes
docker volume rm voicescript_postgres_data 2>/dev/null || true

# Create required directories
mkdir -p certbot/conf certbot/www nginx/conf.d uploads logs
chmod 755 uploads logs
```

### Step 2: Generate Secure Credentials

```bash
# Generate strong SECRET_KEY (copy the output)
openssl rand -hex 32

# Generate database password (copy the output)
openssl rand -hex 16
```

### Step 3: Create .env File

```bash
cat > .env << 'EOF'
# Database Configuration
POSTGRES_PASSWORD=PASTE_GENERATED_PASSWORD_HERE

# Flask Configuration
SECRET_KEY=PASTE_GENERATED_SECRET_KEY_HERE
FLASK_ENV=production

# Security Settings
USE_HTTPS=true
ENABLE_WEBVIEW_FALLBACK=false

# Domain Configuration
DOMAIN=your-domain.com
EMAIL=your@email.com

# Google OAuth (Optional - leave empty if not using)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EOF
```

**Replace:**
- `PASTE_GENERATED_PASSWORD_HERE` with your database password
- `PASTE_GENERATED_SECRET_KEY_HERE` with your secret key
- `your-domain.com` with your actual domain
- `your@email.com` with your email

### Step 4: Update Nginx Configuration

```bash
# Replace placeholder domain with your actual domain
sed -i 's/your-domain\.com/your-actual-domain.com/g' nginx/conf.d/voicescript.conf
```

### Step 5: Configure Firewall

**For UFW (Ubuntu/Debian):**
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8000/tcp   # Block Flask port
sudo ufw deny 5432/tcp   # Block PostgreSQL port
sudo ufw status
```

**For Firewalld (RHEL/CentOS):**
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Step 6: Obtain SSL Certificate (Standalone Method)

```bash
# Get certificate before starting nginx
docker run --rm -p 80:80 \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  -v "$PWD/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --standalone \
  -d your-domain.com -d www.your-domain.com \
  --email your@email.com \
  --agree-tos --no-eff-email
```

**Replace:**
- `your-domain.com` with your actual domain
- `your@email.com` with your email

### Step 7: Start Secure Deployment

```bash
# Start all services
docker-compose -f docker-compose-secure.yml up -d --build

# Wait for services to be ready
sleep 10

# Seed demo data
docker exec -it voicescript_app flask seed-demo --force
```

### Step 8: Verify Installation

```bash
# Check all containers are running
docker-compose -f docker-compose-secure.yml ps

# Check logs for any errors
docker-compose -f docker-compose-secure.yml logs web
docker-compose -f docker-compose-secure.yml logs nginx
```

---

## 🔍 Testing Your Installation

### From External Network (Mobile/Another Computer)

Visit: `https://your-domain.com`

**You should see:**
- 🔒 Secure padlock in browser
- VoiceScript Collector landing page
- No security warnings

### SSL Certificate Validation

Test your SSL setup:
```bash
# Check certificate
curl -I https://your-domain.com

# Or use online tool
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### Session Cookie Security

1. Login via HTTPS
2. Open DevTools → Application → Cookies
3. Verify session cookie has:
   - ✅ `Secure` flag checked
   - ✅ `HttpOnly` flag checked
   - ✅ `SameSite` set to `Lax`

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Rejected request from RFC1918 IP to public server address"

**Cause:** You're accessing your public domain from the same local network (NAT loopback issue)

**Solutions:**
- ✅ Test from external network (mobile with cellular data)
- ✅ Access locally via `http://localhost:8000` or `http://192.168.x.x:8000`
- ✅ Enable NAT loopback/hairpinning on your router

### Issue 2: Database Connection Failed

**Cause:** Old database volume has different password than `.env` file

**Solution:**
```bash
# Clean restart
docker-compose -f docker-compose-secure.yml down
docker volume rm voicescript_postgres_data
docker-compose -f docker-compose-secure.yml up -d --build
docker exec -it voicescript_app flask seed-demo --force
```

### Issue 3: Nginx Fails to Start

**Cause:** SSL certificate files don't exist when nginx starts

**Solution:**
```bash
# Get certificate FIRST using standalone mode
docker-compose -f docker-compose-secure.yml down
docker run --rm -p 80:80 \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly --standalone \
  -d your-domain.com \
  --email your@email.com \
  --agree-tos --no-eff-email

# Then start services
docker-compose -f docker-compose-secure.yml up -d --build
```

### Issue 4: Can't Access from Internet

**Troubleshooting:**
```bash
# Verify DNS points to your server
nslookup your-domain.com

# Check firewall allows 80 and 443
sudo ufw status

# Verify nginx is listening
docker-compose -f docker-compose-secure.yml logs nginx

# Check if ports are accessible
# From external machine:
curl -I http://your-public-ip:80
curl -I http://your-public-ip:443
```

### Issue 5: Used Wrong docker-compose.yml

**Problem:** Ran `docker compose up` instead of `docker-compose -f docker-compose-secure.yml up`

**Solution:**
```bash
# Stop insecure deployment
docker compose down

# Use secure deployment
docker-compose -f docker-compose-secure.yml up -d --build
```

---

## 🔒 Security Checklist

After installation, verify:

- [ ] Application accessible via HTTPS with valid certificate
- [ ] HTTP automatically redirects to HTTPS
- [ ] Session cookies have `Secure` and `HttpOnly` flags
- [ ] Port 8000 (Flask) NOT accessible from internet
- [ ] Port 5432 (PostgreSQL) NOT accessible from internet
- [ ] Firewall configured (only 22, 80, 443 allowed)
- [ ] Strong SECRET_KEY set (32+ characters)
- [ ] Strong database password set (16+ characters)
- [ ] `USE_HTTPS=true` in .env file
- [ ] `ENABLE_WEBVIEW_FALLBACK=false` in .env file

---

## 🔄 Maintenance Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose-secure.yml logs -f

# Specific service
docker-compose -f docker-compose-secure.yml logs -f nginx
docker-compose -f docker-compose-secure.yml logs -f web
docker-compose -f docker-compose-secure.yml logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose-secure.yml restart

# Restart specific service
docker-compose -f docker-compose-secure.yml restart nginx
docker-compose -f docker-compose-secure.yml restart web
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose-secure.yml up -d --build
```

### Backup Database
```bash
# Create backup
docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db > backup_$(date +%Y%m%d).sql

# Backup uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### Restore Database
```bash
# Restore from backup
docker exec -i voicescript_postgres psql -U voicescript_user voicescript_db < backup_20250930.sql
```

### Renew SSL Certificate (Manual)
```bash
# Certificates auto-renew every 12 hours via certbot container
# Manual renewal:
docker-compose -f docker-compose-secure.yml run --rm certbot renew
docker-compose -f docker-compose-secure.yml exec nginx nginx -s reload
```

---

## 📚 File Structure

```
voicescript-collector/
├── app.py                          # Flask application
├── models.py                       # Database models
├── Dockerfile                      # Container configuration
├── docker-compose.yml              # LOCAL development (insecure)
├── docker-compose-secure.yml       # PRODUCTION deployment (secure)
├── setup-https.sh                  # Automated HTTPS setup script
├── .env                            # Environment configuration (create this)
├── templates/                      # HTML templates
├── static/                         # CSS, JS, images
├── uploads/                        # User file uploads
├── logs/                           # Application logs
├── nginx/
│   ├── nginx.conf                  # Main nginx config
│   └── conf.d/
│       └── voicescript.conf        # Site configuration (update domain)
├── certbot/
│   ├── conf/                       # SSL certificates
│   └── www/                        # ACME challenge files
└── SECURITY_PUBLIC_DEPLOYMENT.md   # Detailed security guide
```

---

## 🆘 Getting Help

### Check Service Status
```bash
docker-compose -f docker-compose-secure.yml ps
```

### Debugging Steps
1. Check logs: `docker-compose -f docker-compose-secure.yml logs`
2. Verify .env file exists and has correct values
3. Ensure domain DNS points to your server IP
4. Confirm firewall allows ports 80 and 443
5. Test from external network (not local network)

### Clean Reinstall
```bash
# Complete cleanup
docker-compose -f docker-compose-secure.yml down -v
docker system prune -af
rm -rf certbot/conf/* certbot/www/* uploads/* logs/*

# Start fresh
sudo ./setup-https.sh
```

---

## 📝 Important Notes

1. **Never use `docker-compose.yml` for public deployment** - it's insecure (HTTP only)
2. **Always use `docker-compose-secure.yml`** for production with `-f` flag
3. **Test from external network** - local network may block access due to NAT loopback
4. **Backup your .env file** - it contains critical secrets
5. **Monitor logs regularly** - check for suspicious activity
6. **Keep Docker images updated** - `docker-compose -f docker-compose-secure.yml pull`

---

## ✅ Success Indicators

Your installation is successful when:

- ✅ `https://your-domain.com` loads with green padlock 🔒
- ✅ Demo login works from external network
- ✅ Session cookies are secure (Secure + HttpOnly flags)
- ✅ HTTP redirects to HTTPS automatically
- ✅ Ports 8000 and 5432 are not accessible from internet
- ✅ All containers show "Up" status
- ✅ No errors in logs

---

## 🎉 You're Done!

Your VoiceScript Collector is now securely deployed and accessible from anywhere!

**Next Steps:**
1. Share `https://your-domain.com` with your team
2. Users can register or use demo accounts
3. Configure Google OAuth (optional) for social login
4. Set up regular database backups
5. Monitor logs for issues

For more advanced configuration, see `SECURITY_PUBLIC_DEPLOYMENT.md`
