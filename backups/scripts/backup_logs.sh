#!/bin/bash

# Simple Logs Backup Script for Railway TextGather
# Backs up application logs only

set -e

# Configuration
BACKUP_DIR="$(dirname "$0")/../files"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="logs_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📋 Starting Logs Backup...${NC}"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found${NC}"
    exit 1
fi

# Check project link
if ! railway status &> /dev/null; then
    echo -e "${RED}❌ Not linked to Railway project. Run 'railway link'${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo -e "${YELLOW}📦 Backing up logs...${NC}"

# Create temporary directory for logs
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Method 1: Try to backup logs directory using base64 for safe transport
railway ssh "if [ -d /app/logs ]; then tar -czf /tmp/logs.tar.gz -C /app logs && base64 /tmp/logs.tar.gz; else echo 'No logs directory found'; exit 1; fi" | base64 -d > "${BACKUP_PATH}" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Direct logs backup failed, trying alternative methods...${NC}"
    
    # Method 2: Get recent Railway logs
    echo -e "${YELLOW}📋 Fetching Railway service logs...${NC}"
    railway logs --tail=1000 > "${TEMP_DIR}/railway_logs.txt" 2>/dev/null || {
        echo -e "${YELLOW}⚠️ Could not fetch Railway logs${NC}"
        touch "${TEMP_DIR}/railway_logs_unavailable.txt"
    }
    
    # Method 3: Try to list log files
    railway ssh "if [ -d /app/logs ]; then find /app/logs -name '*.log' -o -name '*.txt' 2>/dev/null; fi" > "${TEMP_DIR}/log_files_list.txt" 2>/dev/null || {
        echo -e "${YELLOW}⚠️ Could not list log files${NC}"
    }
    
    # Method 4: Try to get container logs
    railway ssh "docker logs voicescript_app --tail=100 2>&1 || echo 'Container logs unavailable'" > "${TEMP_DIR}/container_logs.txt" 2>/dev/null || {
        echo -e "${YELLOW}⚠️ Could not get container logs${NC}"
    }
    
    # Create backup with whatever we collected
    echo -e "${YELLOW}📦 Creating logs backup with available data...${NC}"
    
    # Add timestamp and info
    echo "TextGather Logs Backup - $(date)" > "${TEMP_DIR}/backup_info.txt"
    echo "Backup created at: $(date)" >> "${TEMP_DIR}/backup_info.txt"
    echo "Railway project: $(railway status 2>/dev/null | grep 'Project:' || echo 'Unknown')" >> "${TEMP_DIR}/backup_info.txt"
    echo "Service: $(railway status 2>/dev/null | grep 'Service:' || echo 'Unknown')" >> "${TEMP_DIR}/backup_info.txt"
    echo "" >> "${TEMP_DIR}/backup_info.txt"
    
    # Check what we have and add to backup
    FILES_FOUND=0
    if [ -s "${TEMP_DIR}/railway_logs.txt" ]; then
        echo "✅ Railway service logs included" >> "${TEMP_DIR}/backup_info.txt"
        FILES_FOUND=$((FILES_FOUND + 1))
    fi
    
    if [ -s "${TEMP_DIR}/log_files_list.txt" ]; then
        echo "✅ Log files list included" >> "${TEMP_DIR}/backup_info.txt"
        FILES_FOUND=$((FILES_FOUND + 1))
    fi
    
    if [ -s "${TEMP_DIR}/container_logs.txt" ]; then
        echo "✅ Container logs included" >> "${TEMP_DIR}/backup_info.txt"
        FILES_FOUND=$((FILES_FOUND + 1))
    fi
    
    if [ $FILES_FOUND -eq 0 ]; then
        echo "⚠️ No logs could be retrieved" >> "${TEMP_DIR}/backup_info.txt"
        echo "This may be normal if no logs exist yet" >> "${TEMP_DIR}/backup_info.txt"
    fi
    
    # Create the backup archive
    tar -czf "${BACKUP_PATH}" -C "${TEMP_DIR}" . 2>/dev/null || {
        echo -e "${RED}❌ Failed to create logs backup archive${NC}"
        exit 1
    }
}

# Verify backup
if [ -s "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    
    echo -e "${GREEN}✅ Logs backup completed!${NC}"
    echo -e "${GREEN}📁 ${BACKUP_PATH} (${BACKUP_SIZE})${NC}"
    
    # Show backup contents preview
    echo -e "${YELLOW}🔍 Backup contents:${NC}"
    tar -tzf "${BACKUP_PATH}" 2>/dev/null | head -10 || echo "Archive created successfully"
    
    # Show file count
    FILE_COUNT=$(tar -tzf "${BACKUP_PATH}" 2>/dev/null | wc -l || echo "0")
    if [ "$FILE_COUNT" -gt 10 ]; then
        echo "... and $((FILE_COUNT - 10)) more files"
    fi
else
    echo -e "${RED}❌ Logs backup failed${NC}"
    exit 1
fi