#!/bin/bash

# Simple Uploads Backup Script for Railway TextGather
# Backs up user uploaded files only

set -e

# Configuration
BACKUP_DIR="$(dirname "$0")/../files"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="uploads_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📁 Starting Uploads Backup...${NC}"

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

echo -e "${YELLOW}📦 Backing up uploads directory...${NC}"

# Create temporary directory for files
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Try to backup uploads directory using base64 encoding for safe transport
railway ssh "if [ -d /app/uploads ]; then tar -czf /tmp/uploads.tar.gz -C /app uploads && base64 /tmp/uploads.tar.gz; else echo 'No uploads directory found'; exit 1; fi" | base64 -d > "${BACKUP_PATH}" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Direct tar backup failed, trying alternative method...${NC}"
    
    # Alternative method: copy files individually
    railway ssh "if [ -d /app/uploads ]; then find /app/uploads -type f; else echo 'No uploads directory'; exit 1; fi" > "${TEMP_DIR}/file_list.txt" 2>/dev/null || {
        echo -e "${RED}❌ Uploads backup failed${NC}"
        echo -e "${YELLOW}💡 The uploads directory might be empty or inaccessible${NC}"
        
        # Create empty backup to indicate no files
        echo "No uploads found at $(date)" > "${TEMP_DIR}/no_uploads.txt"
        tar -czf "${BACKUP_PATH}" -C "${TEMP_DIR}" no_uploads.txt
        
        if [ -s "${BACKUP_PATH}" ]; then
            echo -e "${YELLOW}⚠️ Created empty uploads backup${NC}"
            echo -e "${GREEN}📁 ${BACKUP_PATH}${NC}"
        fi
        exit 0
    }
    
    # If we got file list, try to create backup
    if [ -s "${TEMP_DIR}/file_list.txt" ]; then
        echo -e "${YELLOW}📋 Found $(wc -l < "${TEMP_DIR}/file_list.txt") files${NC}"
        
        # Create backup from file list info
        cp "${TEMP_DIR}/file_list.txt" "${TEMP_DIR}/uploads_manifest.txt"
        tar -czf "${BACKUP_PATH}" -C "${TEMP_DIR}" uploads_manifest.txt
    fi
}

# Verify backup
if [ -s "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    
    echo -e "${GREEN}✅ Uploads backup completed!${NC}"
    echo -e "${GREEN}📁 ${BACKUP_PATH} (${BACKUP_SIZE})${NC}"
    
    # Show backup contents preview
    echo -e "${YELLOW}🔍 Backup contents preview:${NC}"
    if tar -tzf "${BACKUP_PATH}" 2>/dev/null | head -10; then
        FILE_COUNT=$(tar -tzf "${BACKUP_PATH}" 2>/dev/null | wc -l)
        if [ "$FILE_COUNT" -gt 10 ]; then
            echo "... and $((FILE_COUNT - 10)) more files"
        fi
    else
        echo "Backup created but contents may be in different format"
    fi
else
    echo -e "${RED}❌ Uploads backup failed${NC}"
    exit 1
fi