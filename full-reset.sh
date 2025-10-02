#!/bin/bash

# VoiceScript Collector - Full Reset Script
# Completely wipes and recreates the Docker deployment

set -e

echo "========================================="
echo "VoiceScript Collector - Full Reset"
echo "========================================="
echo ""
echo "⚠️  WARNING: This will DELETE all data!"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Stop and remove EVERYTHING
echo ""
echo "🛑 Stopping and removing all containers and volumes..."
docker-compose -f docker-compose-secure.yml down -v

# Generate secure credentials
echo ""
echo "🔐 Generating secure credentials..."
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Get domain info
echo ""
read -p "Enter your domain (e.g., textgather.duckdns.org): " DOMAIN
read -p "Enter your email: " EMAIL

# Create .env file
echo ""
echo "📄 Creating .env file..."
cat > .env << EOF
# PRODUCTION CONFIGURATION
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
USE_HTTPS=true
ENABLE_WEBVIEW_FALLBACK=false
DOMAIN=$DOMAIN
EMAIL=$EMAIL
UPLOAD_FOLDER=/app/uploads
PORT=8000
EOF

echo "✅ .env file created"

# Fix permissions
echo ""
echo "📁 Creating directories and fixing permissions..."
# Remove if they exist as files (not directories)
[ -f logs ] && rm -f logs
[ -f uploads ] && rm -f uploads
mkdir -p logs uploads certbot/conf certbot/www
chmod -R 777 logs uploads certbot
echo "✅ Directories ready"

# Check if SSL certificates exist
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo ""
    echo "⚠️  SSL certificates not found. Running SSL setup first..."
    echo ""
    
    # Run SSL setup with domain and email passed as arguments
    if [ -f "./setup-https.sh" ]; then
        ./setup-https.sh "$DOMAIN" "$EMAIL"
    else
        echo "❌ setup-https.sh not found. Please run it manually after this script."
        echo "   Then restart with: docker-compose -f docker-compose-secure.yml restart nginx"
    fi
fi

# Start services
echo ""
echo "🚀 Building and starting containers..."
docker-compose -f docker-compose-secure.yml up -d --build

# Wait for database
echo ""
echo "⏳ Waiting for database to initialize..."
sleep 15

# Seed demo data
echo ""
echo "📊 Seeding demo data..."
docker exec voicescript_app flask seed-demo --force --yes

echo ""
echo "========================================="
echo "✅ Full Reset Complete!"
echo "========================================="
echo ""
echo "🌐 Application URL: https://$DOMAIN"
echo ""
echo "🔐 Demo Accounts (password: demo123):"
echo "   Admin:    admin@demo.com"
echo "   Reviewer: reviewer@demo.com"
echo "   Provider: provider@demo.com"
echo ""
echo "🔧 View logs: docker-compose -f docker-compose-secure.yml logs -f"
echo ""
