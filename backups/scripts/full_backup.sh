#!/bin/bash

# Simple Main Backup Script for Railway TextGather
# Runs database, uploads, and logs backups

set -e

# Configuration
SCRIPT_DIR="$(dirname "$0")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_LOG="${SCRIPT_DIR}/../backup_${TIMESTAMP}.log"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}🚀 TextGather Backup Starting...${NC}" | tee "${BACKUP_LOG}"
echo -e "${YELLOW}Timestamp: $(date)${NC}" | tee -a "${BACKUP_LOG}"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found${NC}" | tee -a "${BACKUP_LOG}"
    exit 1
fi

# Check project link
if ! railway status &> /dev/null; then
    echo -e "${RED}❌ Not linked to Railway project. Run 'railway link'${NC}" | tee -a "${BACKUP_LOG}"
    exit 1
fi

# Make scripts executable
chmod +x "${SCRIPT_DIR}"/*.sh

# Track successes
SUCCESS_COUNT=0
TOTAL_BACKUPS=3

# 1. Database Backup
echo -e "${BOLD}${YELLOW}===== DATABASE BACKUP =====${NC}" | tee -a "${BACKUP_LOG}"
if "${SCRIPT_DIR}/backup_database.sh" 2>&1 | tee -a "${BACKUP_LOG}"; then
    echo -e "${GREEN}✅ Database backup completed${NC}" | tee -a "${BACKUP_LOG}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
else
    echo -e "${RED}❌ Database backup failed${NC}" | tee -a "${BACKUP_LOG}"
fi

echo "" | tee -a "${BACKUP_LOG}"

# 2. Uploads Backup
echo -e "${BOLD}${YELLOW}===== UPLOADS BACKUP =====${NC}" | tee -a "${BACKUP_LOG}"
if "${SCRIPT_DIR}/backup_uploads.sh" 2>&1 | tee -a "${BACKUP_LOG}"; then
    echo -e "${GREEN}✅ Uploads backup completed${NC}" | tee -a "${BACKUP_LOG}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
else
    echo -e "${RED}❌ Uploads backup failed${NC}" | tee -a "${BACKUP_LOG}"
fi

echo "" | tee -a "${BACKUP_LOG}"

# 3. Logs Backup
echo -e "${BOLD}${YELLOW}===== LOGS BACKUP =====${NC}" | tee -a "${BACKUP_LOG}"
if "${SCRIPT_DIR}/backup_logs.sh" 2>&1 | tee -a "${BACKUP_LOG}"; then
    echo -e "${GREEN}✅ Logs backup completed${NC}" | tee -a "${BACKUP_LOG}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
else
    echo -e "${RED}❌ Logs backup failed${NC}" | tee -a "${BACKUP_LOG}"
fi

echo "" | tee -a "${BACKUP_LOG}"

# Summary
echo -e "${BOLD}${BLUE}===== BACKUP SUMMARY =====${NC}" | tee -a "${BACKUP_LOG}"
echo -e "${YELLOW}Successful: ${SUCCESS_COUNT}/${TOTAL_BACKUPS}${NC}" | tee -a "${BACKUP_LOG}"

# Show results
echo -e "${YELLOW}📁 Backup locations:${NC}" | tee -a "${BACKUP_LOG}"
ls -la "${SCRIPT_DIR}/../database/" 2>/dev/null | tail -1 | tee -a "${BACKUP_LOG}" || echo "No database backup" | tee -a "${BACKUP_LOG}"
ls -la "${SCRIPT_DIR}/../files/" 2>/dev/null | tail -2 | tee -a "${BACKUP_LOG}" || echo "No files backup" | tee -a "${BACKUP_LOG}"

TOTAL_SIZE=$(du -sh "${SCRIPT_DIR}/../" 2>/dev/null | cut -f1 || echo "Unknown")
echo -e "${BLUE}📊 Total size: ${TOTAL_SIZE}${NC}" | tee -a "${BACKUP_LOG}"

if [ ${SUCCESS_COUNT} -eq ${TOTAL_BACKUPS} ]; then
    echo -e "${BOLD}${GREEN}🎉 All backups completed successfully!${NC}" | tee -a "${BACKUP_LOG}"
    exit 0
elif [ ${SUCCESS_COUNT} -gt 0 ]; then
    echo -e "${YELLOW}⚠️ Partial backup (${SUCCESS_COUNT}/${TOTAL_BACKUPS} successful)${NC}" | tee -a "${BACKUP_LOG}"
    exit 1
else
    echo -e "${RED}❌ All backups failed${NC}" | tee -a "${BACKUP_LOG}"
    exit 2
fi
