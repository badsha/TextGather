# Secure Public Deployment Guide

## ⚠️ CRITICAL: Your Current Setup is NOT Secure

If your application is accessible via a public IP from the internet, you **MUST** follow this guide to secure it properly.

### Current Risks (with USE_HTTPS=false on public IP):
- 🔴 **Passwords transmitted in plaintext** - anyone on the network can intercept them
- 🔴 **Session cookies not secure** - vulnerable to session hijacking
- 🔴 **Database exposed** - port 5432 open to brute force attacks
- 🔴 **No encryption** - all application traffic visible to attackers

---

## 🛡️ Secure Deployment (HTTPS with Let's Encrypt)

### Prerequisites

1. **Domain name** pointing to your server's public IP
   - Required for Let's Encrypt SSL certificate
   - Configure DNS A record: `example.com` → `Your Public IP`
   - Configure DNS A record: `www.example.com` → `Your Public IP`

2. **Server requirements**
   - Public IP address
   - Ports 80 and 443 accessible from internet
   - Docker and Docker Compose installed
   - Root/sudo access for firewall configuration

3. **Close dangerous ports**
   - Port 8000 (Flask) must NOT be exposed
   - Port 5432 (PostgreSQL) must NOT be exposed

---

## 🚀 Automated HTTPS Setup (Recommended)

### Step 1: Prepare

```bash
# Stop current insecure deployment
docker-compose down

# Make setup script executable
chmod +x setup-https.sh
```

### Step 2: Run Setup Script

```bash
# Run with sudo (needed for firewall)
sudo ./setup-https.sh
```

The script will:
1. ✅ Generate strong SECRET_KEY and database password
2. ✅ Configure nginx with your domain
3. ✅ Set up Let's Encrypt SSL certificate
4. ✅ Configure firewall (block 8000, 5432; allow 22, 80, 443)
5. ✅ Deploy secure Docker stack
6. ✅ Enable automatic SSL renewal

### Step 3: Verify

Visit your domain:
- `https://your-domain.com` → Should load securely (🔒 in browser)
- `http://your-domain.com` → Should redirect to HTTPS

Test demo login:
- `https://your-domain.com/login?demo=provider`

---

## 🔧 Manual HTTPS Setup

If you prefer manual setup:

### 1. Create Secure Environment File

```bash
# Generate strong SECRET_KEY
openssl rand -hex 32

# Generate database password
openssl rand -hex 16

# Create .env file
cat > .env << EOF
POSTGRES_PASSWORD=<generated-password>
SECRET_KEY=<generated-secret-key>
FLASK_ENV=production
USE_HTTPS=true
ENABLE_WEBVIEW_FALLBACK=false
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com
EOF
```

### 2. Update Nginx Configuration

Edit `nginx/conf.d/voicescript.conf`:
- Replace `your-domain.com` with your actual domain (3 places)

### 3. Configure Firewall

```bash
# UFW (Ubuntu/Debian)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8000/tcp   # Block Flask
sudo ufw deny 5432/tcp   # Block PostgreSQL
sudo ufw status

# Firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp --remove
sudo firewall-cmd --permanent --add-port=5432/tcp --remove
sudo firewall-cmd --reload
```

### 4. Start Secure Stack

```bash
# Create directories
mkdir -p certbot/conf certbot/www nginx/conf.d uploads logs

# Start services
docker-compose -f docker-compose-secure.yml up -d --build
```

### 5. Obtain SSL Certificate

```bash
# Test with dry run first
docker-compose -f docker-compose-secure.yml run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email your@email.com \
    --agree-tos --no-eff-email \
    --dry-run \
    -d your-domain.com -d www.your-domain.com

# If successful, get real certificate
docker-compose -f docker-compose-secure.yml run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email your@email.com \
    --agree-tos --no-eff-email \
    -d your-domain.com -d www.your-domain.com

# Reload nginx
docker-compose -f docker-compose-secure.yml exec nginx nginx -s reload
```

### 6. Seed Demo Data

```bash
docker exec -it voicescript_app flask seed-demo --force
```

---

## 🔒 Security Checklist

### Required Security Measures:

- [ ] **HTTPS enabled** via Let's Encrypt or commercial SSL
- [ ] **USE_HTTPS=true** in environment variables
- [ ] **Strong SECRET_KEY** (32+ random characters)
- [ ] **Strong database password** (16+ random characters)
- [ ] **Firewall configured** (only 22, 80, 443 allowed)
- [ ] **Port 8000 blocked** from internet (Flask internal only)
- [ ] **Port 5432 blocked** from internet (DB internal only)
- [ ] **ENABLE_WEBVIEW_FALLBACK=false** (no fallback auth)
- [ ] **HSTS header enabled** (in nginx config)
- [ ] **Secure cookies enabled** (automatic with USE_HTTPS=true)

### Recommended Additional Security:

- [ ] **Fail2ban** installed and configured for SSH
- [ ] **Regular backups** automated (database + uploads)
- [ ] **Log monitoring** configured
- [ ] **Rate limiting** enabled for login endpoints (in nginx)
- [ ] **Google OAuth** configured with HTTPS redirect URIs
- [ ] **Security headers** enabled (CSP, X-Frame-Options, etc.)
- [ ] **Regular updates** of Docker images and system packages
- [ ] **Monitoring** setup (Prometheus, Grafana, etc.)

---

## 🔍 Verification Steps

### 1. Check HTTPS is Working

```bash
# Should return 200 with HTTPS
curl -I https://your-domain.com

# Should redirect to HTTPS
curl -I http://your-domain.com
```

### 2. Verify Ports are Secured

```bash
# From external machine - these should FAIL:
curl http://your-ip:8000     # Should timeout/refuse
curl http://your-ip:5432     # Should timeout/refuse

# From external machine - these should WORK:
curl https://your-domain.com  # Should return 200
```

### 3. Test SSL Certificate

Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

Should get A or A+ rating.

### 4. Verify Session Security

1. Login to your app via HTTPS
2. Open browser DevTools → Application → Cookies
3. Verify session cookie has:
   - `Secure`: ✅ (checked)
   - `HttpOnly`: ✅ (checked)
   - `SameSite`: `Lax` or `Strict`

---

## 🔄 Maintenance

### SSL Certificate Renewal

Certificates auto-renew via the certbot container every 12 hours.

Manual renewal:
```bash
docker-compose -f docker-compose-secure.yml run --rm certbot renew
docker-compose -f docker-compose-secure.yml exec nginx nginx -s reload
```

### Backup Important Data

```bash
# Backup database
docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db > backup.sql

# Backup uploads
tar -czf uploads_backup.tar.gz uploads/

# Backup configuration
cp .env .env.backup
```

### View Logs

```bash
# All services
docker-compose -f docker-compose-secure.yml logs -f

# Specific service
docker-compose -f docker-compose-secure.yml logs -f nginx
docker-compose -f docker-compose-secure.yml logs -f web
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose-secure.yml restart

# Restart specific service
docker-compose -f docker-compose-secure.yml restart nginx
```

---

## ⚠️ Common Mistakes to Avoid

1. **❌ Using USE_HTTPS=false on public IP**
   - Exposes passwords and sessions to attackers

2. **❌ Exposing ports 8000 or 5432 to internet**
   - Direct access to Flask or PostgreSQL is dangerous

3. **❌ Weak SECRET_KEY**
   - Use minimum 32 random characters

4. **❌ Not configuring firewall**
   - Always block unnecessary ports

5. **❌ Using self-signed certificates in production**
   - Browsers will show warnings, OAuth will fail

6. **❌ Forgetting to update OAuth redirect URIs**
   - Update Google OAuth to use https://your-domain.com/callback/google

---

## 🆘 Troubleshooting

### SSL Certificate Issues

**Problem**: Certificate not issued
```bash
# Check Let's Encrypt logs
docker-compose -f docker-compose-secure.yml logs certbot

# Verify DNS is pointing to your server
nslookup your-domain.com

# Check port 80 is accessible
curl -I http://your-domain.com/.well-known/acme-challenge/test
```

### Firewall Blocking Everything

```bash
# Check firewall status
sudo ufw status verbose

# Reset if needed (CAUTION: may lock you out via SSH!)
sudo ufw reset
sudo ufw allow 22/tcp  # Allow SSH first!
sudo ufw enable
```

### Sessions Still Not Working

1. Verify USE_HTTPS=true in container:
   ```bash
   docker exec voicescript_app env | grep USE_HTTPS
   ```

2. Check nginx is forwarding headers:
   ```bash
   docker-compose -f docker-compose-secure.yml logs nginx | grep X-Forwarded
   ```

3. Clear browser cookies and try again

---

## 📚 Additional Resources

- **Let's Encrypt Documentation**: https://letsencrypt.org/docs/
- **Nginx SSL Configuration**: https://ssl-config.mozilla.org/
- **SSL Test**: https://www.ssllabs.com/ssltest/
- **Security Headers**: https://securityheaders.com/

---

## 🚨 Emergency Rollback

If something goes wrong:

```bash
# Stop secure deployment
docker-compose -f docker-compose-secure.yml down

# Start basic deployment (INSECURE - local only!)
docker-compose up -d

# Access at http://localhost:8000
```

**Note**: Only use insecure deployment for local testing, never on public IP!
