#!/bin/bash

# Simple Database Backup Script for Railway TextGather
# Backs up PostgreSQL database only

set -e

# Configuration
BACKUP_DIR="$(dirname "$0")/../database"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="database_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}💾 Starting Database Backup...${NC}"

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

echo -e "${YELLOW}📊 Backing up database...${NC}"

# Try to backup database
railway ssh "pg_dump postgresql://voicescript_user:\${POSTGRES_PASSWORD:-voicescript_password}@postgres:5432/voicescript_db" > "${BACKUP_PATH}" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Direct pg_dump failed, trying container method...${NC}"
    railway ssh "docker exec voicescript_postgres pg_dump -U voicescript_user voicescript_db" > "${BACKUP_PATH}" 2>/dev/null || {
        echo -e "${RED}❌ Database backup failed${NC}"
        echo -e "${YELLOW}💡 Try exporting from Railway dashboard${NC}"
        rm -f "${BACKUP_PATH}"
        exit 1
    }
}

# Verify and compress backup
if [ -s "${BACKUP_PATH}" ]; then
    echo -e "${YELLOW}🗜️ Compressing backup...${NC}"
    gzip "${BACKUP_PATH}"
    COMPRESSED_PATH="${BACKUP_PATH}.gz"
    BACKUP_SIZE=$(du -h "${COMPRESSED_PATH}" | cut -f1)
    
    echo -e "${GREEN}✅ Database backup completed!${NC}"
    echo -e "${GREEN}📁 ${COMPRESSED_PATH} (${BACKUP_SIZE})${NC}"
else
    echo -e "${RED}❌ Backup failed${NC}"
    rm -f "${BACKUP_PATH}"
    exit 1
fi
