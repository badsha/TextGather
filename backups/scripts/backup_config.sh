#!/bin/bash

# Optional Configuration Backup Script for Railway TextGather
# Backs up nginx config, SSL certificates, and other system files
# This is an advanced backup for configuration files

set -e

# Configuration
BACKUP_DIR="$(dirname "$0")/../files"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="config_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⚙️ Starting Configuration Backup...${NC}"
echo -e "${YELLOW}This backs up nginx config, SSL certs, and system files${NC}"

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

echo -e "${YELLOW}📦 Collecting configuration files...${NC}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Create info file
echo "TextGather Configuration Backup - $(date)" > "${TEMP_DIR}/config_backup_info.txt"
echo "====================================" >> "${TEMP_DIR}/config_backup_info.txt"
echo "" >> "${TEMP_DIR}/config_backup_info.txt"

CONFIG_ITEMS=0

# 1. Try to backup nginx configuration
echo -e "${YELLOW}🌐 Backing up nginx configuration...${NC}"
railway ssh "if [ -d /etc/nginx ]; then tar -czf /tmp/nginx_config.tar.gz -C /etc nginx && cat /tmp/nginx_config.tar.gz; else echo 'nginx config not accessible'; exit 1; fi" > "${TEMP_DIR}/nginx_config.tar.gz" 2>/dev/null && {
    echo "✅ Nginx configuration backed up" >> "${TEMP_DIR}/config_backup_info.txt"
    CONFIG_ITEMS=$((CONFIG_ITEMS + 1))
    echo -e "${GREEN}✅ Nginx config backed up${NC}"
} || {
    echo "⚠️ Nginx configuration not accessible" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ Nginx config not accessible${NC}"
}

# 2. Try to backup SSL certificates
echo -e "${YELLOW}🔒 Backing up SSL certificates...${NC}"
railway ssh "if [ -d /etc/letsencrypt ]; then tar -czf /tmp/ssl_certs.tar.gz -C /etc letsencrypt && cat /tmp/ssl_certs.tar.gz; else echo 'SSL certs not accessible'; exit 1; fi"
    echo "✅ SSL certificates backed up" >> "${TEMP_DIR}/config_backup_info.txt"
    CONFIG_ITEMS=$((CONFIG_ITEMS + 1))
    echo -e "${GREEN}✅ SSL certificates backed up${NC}"
} || {
    echo "⚠️ SSL certificates not accessible" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ SSL certificates not accessible${NC}"
}

# 3. Get environment variables (without sensitive data)
echo -e "${YELLOW}🔧 Collecting environment information...${NC}"
railway ssh "env | grep -E '^(FLASK|RAILWAY|DATABASE_URL)' | sed 's/=.*/=***REDACTED***/' || echo 'env not accessible'"
    echo "✅ Environment variables list (redacted) saved" >> "${TEMP_DIR}/config_backup_info.txt"
    CONFIG_ITEMS=$((CONFIG_ITEMS + 1))
    echo -e "${GREEN}✅ Environment info collected${NC}"
} || {
    echo "⚠️ Environment variables not accessible" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ Environment info not accessible${NC}"
}

# 4. Get system information
echo -e "${YELLOW}💻 Collecting system information...${NC}"
railway ssh "echo '=== SYSTEM INFO ===' && uname -a && echo && echo '=== DISK USAGE ===' && df -h && echo && echo '=== RUNNING PROCESSES ===' && ps aux | head -20"
    echo "✅ System information saved" >> "${TEMP_DIR}/config_backup_info.txt"
    CONFIG_ITEMS=$((CONFIG_ITEMS + 1))
    echo -e "${GREEN}✅ System info collected${NC}"
} || {
    echo "⚠️ System information not accessible" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ System info not accessible${NC}"
}

# 5. Get Docker information
echo -e "${YELLOW}🐳 Collecting Docker information...${NC}"
railway ssh "echo '=== DOCKER CONTAINERS ===' && docker ps -a && echo && echo '=== DOCKER IMAGES ===' && docker images && echo && echo '=== DOCKER NETWORKS ===' && docker network ls"
    echo "✅ Docker information saved" >> "${TEMP_DIR}/config_backup_info.txt"
    CONFIG_ITEMS=$((CONFIG_ITEMS + 1))
    echo -e "${GREEN}✅ Docker info collected${NC}"
} || {
    echo "⚠️ Docker information not accessible" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ Docker info not accessible${NC}"
}

# 6. Backup local configuration files
echo -e "${YELLOW}📄 Adding local configuration files...${NC}"
LOCAL_CONFIGS=0

# Add docker-compose files
for file in docker-compose*.yml Dockerfile* nginx.conf *.env.example; do
    if [ -f "$file" ]; then
        cp "$file" "${TEMP_DIR}/" 2>/dev/null && {
            LOCAL_CONFIGS=$((LOCAL_CONFIGS + 1))
        }
    fi
done

if [ -d "nginx" ]; then
    cp -r nginx "${TEMP_DIR}/" 2>/dev/null && {
        LOCAL_CONFIGS=$((LOCAL_CONFIGS + 1))
    }
fi

if [ $LOCAL_CONFIGS -gt 0 ]; then
    echo "✅ $LOCAL_CONFIGS local configuration files added" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${GREEN}✅ Local config files added${NC}"
else
    echo "⚠️ No local configuration files found" >> "${TEMP_DIR}/config_backup_info.txt"
    echo -e "${YELLOW}⚠️ No local config files found${NC}"
fi

# 7. Add Railway service information
echo -e "${YELLOW}🚂 Adding Railway service information...${NC}"
railway status > "${TEMP_DIR}/railway_status.txt" 2>/dev/null || echo "Railway status unavailable" > "${TEMP_DIR}/railway_status.txt"
railway variables > "${TEMP_DIR}/railway_variables.txt" 2>/dev/null || echo "Railway variables unavailable" > "${TEMP_DIR}/railway_variables.txt"

echo "✅ Railway service information added" >> "${TEMP_DIR}/config_backup_info.txt"
echo -e "${GREEN}✅ Railway info added${NC}"

# Summary
echo "" >> "${TEMP_DIR}/config_backup_info.txt"
echo "Configuration items backed up: $CONFIG_ITEMS" >> "${TEMP_DIR}/config_backup_info.txt"
echo "Local files added: $LOCAL_CONFIGS" >> "${TEMP_DIR}/config_backup_info.txt"
echo "Backup completed: $(date)" >> "${TEMP_DIR}/config_backup_info.txt"

# Create the backup archive
echo -e "${YELLOW}🗜️ Creating configuration backup archive...${NC}"
tar -czf "${BACKUP_PATH}" -C "${TEMP_DIR}" . 2>/dev/null || {
    echo -e "${RED}❌ Failed to create configuration backup${NC}"
    exit 1
}

# Verify backup
if [ -s "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    
    echo -e "${GREEN}✅ Configuration backup completed!${NC}"
    echo -e "${GREEN}📁 ${BACKUP_PATH} (${BACKUP_SIZE})${NC}"
    
    echo -e "${YELLOW}📋 What was backed up:${NC}"
    if [ $CONFIG_ITEMS -gt 0 ]; then
        echo -e "   • $CONFIG_ITEMS configuration components"
    fi
    if [ $LOCAL_CONFIGS -gt 0 ]; then
        echo -e "   • $LOCAL_CONFIGS local configuration files"
    fi
    echo -e "   • Railway service information"
    echo -e "   • System and Docker information"
    
    echo -e "${YELLOW}🔍 Backup contents:${NC}"
    tar -tzf "${BACKUP_PATH}" | head -10
    FILE_COUNT=$(tar -tzf "${BACKUP_PATH}" | wc -l)
    if [ "$FILE_COUNT" -gt 10 ]; then
        echo "... and $((FILE_COUNT - 10)) more files"
    fi
else
    echo -e "${RED}❌ Configuration backup failed${NC}"
    exit 1
fi

echo -e "${BLUE}💡 Note: This backup contains system configuration files${NC}"
echo -e "${BLUE}   Store it securely as it may contain sensitive information${NC}"