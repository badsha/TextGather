#!/bin/bash

# Railway Files Backup Script for Multi-Container Service
# This script backs up uploaded files, logs, and other persistent data from your Railway deployment

set -e  # Exit on any error

# Configuration
BACKUP_DIR="$(dirname "$0")/../files"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILES_BACKUP="textgather_files_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${FILES_BACKUP}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Railway Files Backup...${NC}"

# Check if railway CLI is available
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if we're linked to a Railway project
if ! railway status &> /dev/null; then
    echo -e "${RED}❌ Not linked to a Railway project. Run 'railway link' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📊 Railway Status:${NC}"
railway status

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo -e "${YELLOW}💾 Creating files backup...${NC}"

# Create temporary directory for collecting files
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

echo -e "${BLUE}📁 Collecting files from Railway service...${NC}"

# Method 1: Try to copy files using railway shell
echo -e "${YELLOW}Attempting to backup uploads directory...${NC}"
railway shell -c "tar -czf /tmp/uploads_backup.tar.gz -C /app uploads 2>/dev/null && cat /tmp/uploads_backup.tar.gz" > "${TEMP_DIR}/uploads.tar.gz" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Direct uploads backup failed, trying alternative method...${NC}"
    
    # Alternative: Try copying individual files
    railway shell -c "if [ -d /app/uploads ]; then find /app/uploads -type f -exec cat {} \\; 2>/dev/null; else echo 'No uploads directory found'; fi" > "${TEMP_DIR}/uploads_raw.txt" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Uploads directory might be empty or inaccessible${NC}"
        touch "${TEMP_DIR}/uploads_empty.txt"
    }
}

echo -e "${YELLOW}Attempting to backup logs directory...${NC}"
railway shell -c "tar -czf /tmp/logs_backup.tar.gz -C /app logs 2>/dev/null && cat /tmp/logs_backup.tar.gz" > "${TEMP_DIR}/logs.tar.gz" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Direct logs backup failed, trying to get recent logs...${NC}"
    
    # Get logs via railway logs command
    echo -e "${BLUE}📋 Fetching recent application logs...${NC}"
    railway logs --tail=1000 > "${TEMP_DIR}/recent_logs.txt" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not fetch logs${NC}"
        touch "${TEMP_DIR}/logs_empty.txt"
    }
}

# Method 2: Try to get nginx configuration if accessible
echo -e "${YELLOW}Attempting to backup nginx configuration...${NC}"
railway shell -c "tar -czf /tmp/nginx_backup.tar.gz -C / etc/nginx 2>/dev/null && cat /tmp/nginx_backup.tar.gz" > "${TEMP_DIR}/nginx_config.tar.gz" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Nginx config backup failed (might not be accessible)${NC}"
    touch "${TEMP_DIR}/nginx_config_unavailable.txt"
}

# Method 3: Try to backup SSL certificates if accessible
echo -e "${YELLOW}Attempting to backup SSL certificates...${NC}"
railway shell -c "tar -czf /tmp/certs_backup.tar.gz -C / etc/letsencrypt 2>/dev/null && cat /tmp/certs_backup.tar.gz" > "${TEMP_DIR}/ssl_certs.tar.gz" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  SSL certificates backup failed (might not be accessible)${NC}"
    touch "${TEMP_DIR}/ssl_certs_unavailable.txt"
}

# Get system information and environment details
echo -e "${BLUE}📊 Collecting system information...${NC}"
railway shell -c "echo '=== SYSTEM INFO ===' && uname -a && echo && echo '=== DISK USAGE ===' && df -h && echo && echo '=== RUNNING PROCESSES ===' && ps aux" > "${TEMP_DIR}/system_info.txt" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Could not get system information${NC}"
}

# Get docker container information
railway shell -c "echo '=== DOCKER CONTAINERS ===' && docker ps -a && echo && echo '=== DOCKER IMAGES ===' && docker images" > "${TEMP_DIR}/docker_info.txt" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Could not get docker information${NC}"
}

# Create service configuration backup
echo -e "${BLUE}⚙️  Creating configuration backup...${NC}"
cat > "${TEMP_DIR}/service_config.txt" << EOF
=== RAILWAY SERVICE CONFIGURATION ===
Backup Date: $(date)
Project: $(railway status 2>/dev/null | grep "Project:" | cut -d' ' -f2- || echo "Unknown")
Environment: $(railway status 2>/dev/null | grep "Environment:" | cut -d' ' -f2- || echo "Unknown")
Service: $(railway status 2>/dev/null | grep "Service:" | cut -d' ' -f2- || echo "Unknown")

=== LOCAL DOCKER-COMPOSE CONFIGURATION ===
EOF

# Add docker-compose files to backup
if [ -f "docker-compose-secure.yml" ]; then
    echo "docker-compose-secure.yml found - adding to backup"
    cp "docker-compose-secure.yml" "${TEMP_DIR}/"
fi

if [ -f "docker-compose.yml" ]; then
    echo "docker-compose.yml found - adding to backup"
    cp "docker-compose.yml" "${TEMP_DIR}/"
fi

if [ -f "Dockerfile" ]; then
    echo "Dockerfile found - adding to backup"
    cp "Dockerfile" "${TEMP_DIR}/"
fi

# Create the final backup archive
echo -e "${YELLOW}🗜️  Creating final backup archive...${NC}"
cd "${TEMP_DIR}"
tar -czf "${BACKUP_PATH}" . 2>/dev/null

# Verify backup was created
if [ -s "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}✅ Files backup completed successfully!${NC}"
    echo -e "${GREEN}📁 Backup saved to: ${BACKUP_PATH}${NC}"
    echo -e "${GREEN}📊 Backup size: ${BACKUP_SIZE}${NC}"
    
    # Show contents of backup
    echo -e "${YELLOW}🔍 Backup contents:${NC}"
    tar -tzf "${BACKUP_PATH}" | head -20
    
    if [ $(tar -tzf "${BACKUP_PATH}" | wc -l) -gt 20 ]; then
        echo "... and $(($(tar -tzf "${BACKUP_PATH}" | wc -l) - 20)) more files"
    fi
    
else
    echo -e "${RED}❌ Files backup failed or resulted in empty file${NC}"
    rm -f "${BACKUP_PATH}"
    exit 1
fi

echo -e "${GREEN}🎉 Files backup completed successfully!${NC}"
echo -e "${YELLOW}📝 What was backed up:${NC}"
echo -e "   • User uploads (if accessible)"
echo -e "   • Application logs"
echo -e "   • System information"
echo -e "   • Docker configuration"
echo -e "   • Service configuration files"
echo -e "   • SSL certificates (if accessible)"
echo -e ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "   • Backup location: ${BACKUP_PATH}"
echo -e "   • To extract: tar -xzf ${BACKUP_PATH}"
echo -e "   • Consider setting up automated backups with cron"