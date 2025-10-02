#!/bin/bash

DOMAIN="textgather.logiclayerhq.com"

echo "Testing domain: $DOMAIN"
echo "================================"
echo ""

echo "1. DNS Resolution:"
nslookup $DOMAIN
echo ""

echo "2. Testing port 80 accessibility:"
timeout 5 curl -I http://$DOMAIN 2>&1 || echo "Port 80 not accessible"
echo ""

echo "3. Getting Let's Encrypt certificate (dry run):"
docker run --rm -p 80:80 -p 443:443 \
    -v certbot_conf:/etc/letsencrypt \
    -v certbot_www:/var/www/certbot \
    certbot/certbot certonly --standalone --dry-run \
    -d $DOMAIN \
    --email hamid.badsha@gmail.com \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -v

echo ""
echo "================================"
echo "If dry run succeeded, the real certificate will work."
