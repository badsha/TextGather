#!/bin/bash

# Automated Backup Setup Script for Railway TextGather
# This script sets up automated backups using cron jobs

set -e

SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname "$(dirname "$0")")"
CRON_SCRIPT="${SCRIPT_DIR}/cron_backup.sh"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}🔧 Setting up Automated Railway Backups${NC}"
echo -e "${YELLOW}This will create cron jobs to automatically backup your Railway deployment${NC}"

# Create a cron-friendly backup script
cat > "${CRON_SCRIPT}" << 'EOF'
#!/bin/bash

# Cron-friendly backup script
# This script is called by cron jobs

# Set PATH for cron environment
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Change to project directory
cd "$(dirname "$0")/../.."

# Run the full backup
exec "./backups/scripts/full_backup.sh" 2>&1 | logger -t "railway-backup"
EOF

chmod +x "${CRON_SCRIPT}"

echo -e "${GREEN}✅ Cron backup script created: ${CRON_SCRIPT}${NC}"

# Function to show current cron jobs
show_current_cron() {
    echo -e "${YELLOW}Current cron jobs:${NC}"
    crontab -l 2>/dev/null | grep -E "(railway|backup|textgather)" || echo "No existing backup cron jobs found"
}

# Function to add a cron job
add_cron_job() {
    local schedule="$1"
    local description="$2"
    
    # Create the cron job entry
    local cron_entry="${schedule} ${CRON_SCRIPT} # ${description}"
    
    # Add to crontab
    (crontab -l 2>/dev/null || true; echo "${cron_entry}") | crontab -
    
    echo -e "${GREEN}✅ Added cron job: ${description}${NC}"
    echo -e "${BLUE}   Schedule: ${schedule}${NC}"
}

# Function to setup backup retention
setup_retention() {
    local retention_script="${SCRIPT_DIR}/cleanup_old_backups.sh"
    
    cat > "${retention_script}" << 'EOF'
#!/bin/bash

# Backup retention cleanup script
# Keeps only the last N backups to save disk space

BACKUP_DIR="$(dirname "$0")/../"
RETENTION_DAYS=30  # Keep backups for 30 days
MAX_BACKUPS=10     # Keep maximum 10 recent backups

echo "🧹 Cleaning up old backups..."

# Delete backups older than retention period
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "backup_*.log" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

# Keep only the most recent backups in each category
cd "${BACKUP_DIR}"

# Clean database backups
if [ -d "database" ]; then
    cd database
    ls -t *.sql.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm --
    cd ..
fi

# Clean file backups
if [ -d "files" ]; then
    cd files
    ls -t *.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm --
    cd ..
fi

echo "✅ Backup cleanup completed"
EOF

    chmod +x "${retention_script}"
    echo -e "${GREEN}✅ Created retention cleanup script: ${retention_script}${NC}"
}

# Main setup menu
echo ""
echo -e "${BOLD}Choose backup frequency:${NC}"
echo "1) Daily at 2 AM"
echo "2) Every 12 hours (2 AM and 2 PM)"
echo "3) Every 6 hours"
echo "4) Weekly (Sunday at 2 AM)"
echo "5) Custom schedule"
echo "6) Show current cron jobs only"
echo ""

read -p "Enter your choice (1-6): " choice

show_current_cron

case $choice in
    1)
        add_cron_job "0 2 * * *" "Daily Railway TextGather backup at 2 AM"
        ;;
    2)
        add_cron_job "0 2,14 * * *" "Railway TextGather backup every 12 hours"
        ;;
    3)
        add_cron_job "0 2,8,14,20 * * *" "Railway TextGather backup every 6 hours"
        ;;
    4)
        add_cron_job "0 2 * * 0" "Weekly Railway TextGather backup on Sunday at 2 AM"
        ;;
    5)
        echo -e "${YELLOW}Enter custom cron schedule (e.g., '0 3 * * *' for daily at 3 AM):${NC}"
        read -p "Schedule: " custom_schedule
        read -p "Description: " custom_description
        add_cron_job "${custom_schedule}" "${custom_description}"
        ;;
    6)
        echo -e "${GREEN}Current cron jobs displayed above${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Setup retention cleanup
setup_retention

# Add weekly cleanup job
add_cron_job "0 3 * * 1" "Weekly backup cleanup (retention policy)"

echo ""
echo -e "${BOLD}${GREEN}🎉 Automated backup setup completed!${NC}"
echo ""
echo -e "${YELLOW}📝 What was set up:${NC}"
echo -e "   • Automated backup cron job"
echo -e "   • Backup retention cleanup (weekly)"
echo -e "   • Logs sent to system logger"
echo ""
echo -e "${YELLOW}🔧 To manage cron jobs:${NC}"
echo -e "   • View all jobs: ${BOLD}crontab -l${NC}"
echo -e "   • Edit jobs: ${BOLD}crontab -e${NC}"
echo -e "   • Remove jobs: ${BOLD}crontab -r${NC}"
echo ""
echo -e "${YELLOW}📋 To check backup logs:${NC}"
echo -e "   • System logs: ${BOLD}grep 'railway-backup' /var/log/system.log${NC}"
echo -e "   • Backup directory: ${BOLD}ls -la ${PROJECT_DIR}${NC}"
echo ""
echo -e "${BLUE}💡 Pro tip: Test your backup manually first:${NC}"
echo -e "   ${BOLD}${PROJECT_DIR}/scripts/full_backup.sh${NC}"