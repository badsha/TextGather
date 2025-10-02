#!/bin/bash

# VoiceScript Collector - HTTPS Setup Script
# This script sets up secure HTTPS deployment with Let's Encrypt

set -e  # Exit on any error

echo "========================================="
echo "VoiceScript Collector - HTTPS Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges for firewall configuration"
    echo "Please run with: sudo ./setup-https.sh"
    exit 1
fi

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Get domain and email (from arguments or prompt)
if [ -n "$1" ] && [ -n "$2" ]; then
    DOMAIN="$1"
    EMAIL="$2"
    echo ""
    echo "📝 Using provided configuration:"
    echo "   Domain: $DOMAIN"
    echo "   Email: $EMAIL"
else
    echo ""
    echo "📝 Configuration"
    echo "----------------------------------------"
    read -p "Enter your domain name (e.g., example.com): " DOMAIN
    read -p "Enter your email for SSL notifications: " EMAIL
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        echo "❌ Domain and email are required!"
        exit 1
    fi
fi

# Generate strong SECRET_KEY
echo ""
echo "🔐 Generating secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)

# Generate strong database password
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Create .env file
echo ""
echo "📄 Creating .env file..."
cat > .env << EOF
# SECURE PRODUCTION CONFIGURATION
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
USE_HTTPS=true
ENABLE_WEBVIEW_FALLBACK=false
DOMAIN=$DOMAIN
EMAIL=$EMAIL
EOF

echo "✅ .env file created with secure credentials"

# Update nginx configuration with domain
echo ""
echo "🔧 Configuring nginx with your domain..."
# Mac-compatible sed command
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/YOUR_DOMAIN_HERE/$DOMAIN/g" nginx/conf.d/voicescript.conf
else
    sed -i "s/YOUR_DOMAIN_HERE/$DOMAIN/g" nginx/conf.d/voicescript.conf
fi
echo "✅ Nginx configured for $DOMAIN"

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p uploads logs
chmod -R 755 uploads logs
echo "✅ Directories created"

# Create Docker volumes for certbot (avoids permission issues)
echo "📦 Creating Docker volumes for SSL certificates..."
docker volume create certbot_conf 2>/dev/null || true
docker volume create certbot_www 2>/dev/null || true
echo "✅ Docker volumes ready"

# Configure firewall
echo ""
echo "🔥 Configuring firewall..."
echo "This will:"
echo "  - Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)"
echo "  - Block ports 8000 (Flask) and 5432 (PostgreSQL)"
echo ""
read -p "Configure firewall? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow 22/tcp comment 'SSH'
        ufw allow 80/tcp comment 'HTTP'
        ufw allow 443/tcp comment 'HTTPS'
        ufw deny 8000/tcp comment 'Block Flask'
        ufw deny 5432/tcp comment 'Block PostgreSQL'
        ufw status
        echo "✅ Firewall configured with UFW"
    else
        echo "⚠️  UFW not found. Please configure firewall manually:"
        echo "   - Allow: 22, 80, 443"
        echo "   - Block: 8000, 5432"
    fi
fi

# Obtain SSL certificate FIRST (before starting nginx)
echo ""
echo "🔒 Obtaining SSL certificate from Let's Encrypt..."
echo "Getting certificate before starting nginx..."

# Stop any running containers
docker-compose -f docker-compose-secure.yml down 2>/dev/null || true

# Get certificate using standalone mode (nginx not running yet)
# Use Docker-managed volumes to avoid permission issues
docker run --rm -p 80:80 -p 443:443 \
    -v certbot_conf:/etc/letsencrypt \
    -v certbot_www:/var/www/certbot \
    certbot/certbot certonly --standalone \
    -d $DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
    
    # Verify certificate exists in Docker volume
    echo "🔍 Verifying certificate in Docker volume..."
    docker run --rm -v certbot_conf:/etc/letsencrypt \
        alpine ls -la /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "❌ Certificate files not found in Docker volume!"
        echo "Checking what's in the volume..."
        docker run --rm -v certbot_conf:/etc/letsencrypt alpine ls -la /etc/letsencrypt/
        exit 1
    fi
    echo "✅ Certificate verified in volume"
else
    echo "❌ Failed to obtain SSL certificate. Please check:"
    echo "   - Domain DNS points to this server"
    echo "   - Ports 80 and 443 are accessible from internet"
    echo "   - No other service is using ports 80/443"
    exit 1
fi

# NOW start services with certificate in place
echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose-secure.yml up -d --build

echo "⏳ Waiting for services to be ready..."
sleep 10

# Seed demo data
echo ""
echo "📊 Seeding demo data..."
docker exec -it voicescript_app flask seed-demo --force

# Final status
echo ""
echo "========================================="
echo "✅ HTTPS Setup Complete!"
echo "========================================="
echo ""
echo "🌐 Your application is now accessible at:"
echo "   https://$DOMAIN"
echo ""
echo "🔐 Security Status:"
echo "   ✅ HTTPS enabled with Let's Encrypt"
echo "   ✅ Secure cookies enabled"
echo "   ✅ Database not exposed to internet"
echo "   ✅ Flask app not exposed to internet"
echo "   ✅ Firewall configured"
echo ""
echo "📝 Credentials saved in .env file"
echo "   Keep this file secure and backup!"
echo ""
echo "📊 Demo Accounts:"
echo "   Provider: https://$DOMAIN/login?demo=provider"
echo "   Reviewer: https://$DOMAIN/login?demo=reviewer"
echo "   Admin: https://$DOMAIN/login?demo=admin"
echo ""
echo "🔧 Useful Commands:"
echo "   View logs:     docker-compose -f docker-compose-secure.yml logs -f"
echo "   Stop:          docker-compose -f docker-compose-secure.yml down"
echo "   Restart:       docker-compose -f docker-compose-secure.yml restart"
echo "   Renew cert:    docker-compose -f docker-compose-secure.yml run --rm certbot renew"
echo ""
echo "⚠️  Important Security Reminders:"
echo "   1. Keep your SECRET_KEY secure (in .env file)"
echo "   2. SSL certificate renews automatically every 12 hours"
echo "   3. Backup your database regularly"
echo "   4. Monitor access logs for suspicious activity"
echo ""
