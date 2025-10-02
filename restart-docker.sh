#!/bin/bash

# VoiceScript Collector - Docker Restart Script
# Fixes permissions and restarts containers

echo "========================================="
echo "VoiceScript Collector - Docker Restart"
echo "========================================="
echo ""

# Fix permissions
echo "📁 Fixing directory permissions..."
chmod -R 777 logs uploads
mkdir -p logs uploads
echo "✅ Permissions fixed"

# Stop containers
echo ""
echo "🛑 Stopping containers..."
docker-compose -f docker-compose-secure.yml down

# Start containers
echo ""
echo "🚀 Starting containers..."
docker-compose -f docker-compose-secure.yml up -d

# Wait for services
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Show status
echo ""
echo "📊 Container status:"
docker-compose -f docker-compose-secure.yml ps

echo ""
echo "========================================="
echo "✅ Restart Complete!"
echo "========================================="
echo ""
echo "🔧 Useful commands:"
echo "   View logs:  docker-compose -f docker-compose-secure.yml logs -f"
echo "   Stop:       docker-compose -f docker-compose-secure.yml down"
echo ""
