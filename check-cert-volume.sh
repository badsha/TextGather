#!/bin/bash

echo "Checking certbot_conf Docker volume contents:"
echo "=============================================="
echo ""

echo "1. Volume contents:"
docker run --rm -v certbot_conf:/etc/letsencrypt alpine ls -la /etc/letsencrypt/
echo ""

echo "2. Live certificates directory:"
docker run --rm -v certbot_conf:/etc/letsencrypt alpine ls -la /etc/letsencrypt/live/ 2>/dev/null || echo "No live directory"
echo ""

echo "3. Looking for textgather.logiclayerhq.com:"
docker run --rm -v certbot_conf:/etc/letsencrypt alpine ls -la /etc/letsencrypt/live/textgather.logiclayerhq.com/ 2>/dev/null || echo "Domain directory not found"
echo ""

echo "4. Archive directory:"
docker run --rm -v certbot_conf:/etc/letsencrypt alpine ls -la /etc/letsencrypt/archive/ 2>/dev/null || echo "No archive directory"
