# Railway TextGather Backup System

This backup system provides simple, focused backup solutions for your Railway-deployed TextGather application. It backs up only the essential data: database, uploaded files, and logs.

## 📁 Directory Structure

```
backups/
├── README.md                           # This file
├── database/                           # Database backups (.sql.gz files)
├── files/                             # Files backups (.tar.gz files)
└── scripts/                           # Backup scripts
    ├── backup_database.sh             # PostgreSQL database backup
    ├── backup_uploads.sh              # User uploaded files
    ├── backup_logs.sh                 # Application logs
    ├── backup_config.sh               # Optional: nginx, SSL, configs
    ├── full_backup.sh                 # Runs all 3 main backups
    └── setup_automated_backup.sh      # Sets up cron jobs
```

## 🚀 Quick Start

### 1. Manual Backup (Run Once)

```bash
# All essential backups (database + uploads + logs)
./backups/scripts/full_backup.sh

# Individual backups
./backups/scripts/backup_database.sh   # Database only
./backups/scripts/backup_uploads.sh    # Uploaded files only
./backups/scripts/backup_logs.sh       # Application logs only
./backups/scripts/backup_config.sh     # Optional: configs & system files
```

### 2. Setup Automated Backups

```bash
# Interactive setup for scheduled backups
./backups/scripts/setup_automated_backup.sh
```

## 📊 What Gets Backed Up

### Database Backup (`backup_database.sh`)
- ✅ Complete PostgreSQL database dump
- ✅ Compressed with gzip for space efficiency
- ✅ All tables, data, schemas, and relationships
- 📁 Saved to: `backups/database/database_YYYYMMDD_HHMMSS.sql.gz`

### Uploads Backup (`backup_uploads.sh`)
- ✅ User uploaded files from `/app/uploads`
- ✅ File manifest if direct access fails
- 📁 Saved to: `backups/files/uploads_YYYYMMDD_HHMMSS.tar.gz`

### Logs Backup (`backup_logs.sh`)
- ✅ Application logs from `/app/logs`
- ✅ Railway service logs (recent)
- ✅ Container logs (if accessible)
- 📁 Saved to: `backups/files/logs_YYYYMMDD_HHMMSS.tar.gz`

### Configuration Backup (`backup_config.sh`) - *Optional*
- ✅ Nginx configuration (if accessible)
- ✅ SSL certificates (if accessible)
- ✅ Environment variables (redacted)
- ✅ System and Docker information
- ✅ Local docker-compose and config files
- 📁 Saved to: `backups/files/config_YYYYMMDD_HHMMSS.tar.gz`

## ⚙️ Configuration

### Environment Requirements
- ✅ Railway CLI installed and authenticated
- ✅ Project linked to current directory (`railway link`)
- ✅ Internet connection for Railway API access

### Railway Service Structure
Your TextGather service contains multiple containers:
- `nginx` - Web server and SSL termination
- `web` - Flask application (main app)
- `postgres` - PostgreSQL database
- `certbot` - SSL certificate management

## 🔄 Automated Backup Options

The setup script offers several scheduling options:

1. **Daily** - Every day at 2 AM
2. **Twice Daily** - Every 12 hours (2 AM, 2 PM)
3. **Every 6 Hours** - 4 times daily (2 AM, 8 AM, 2 PM, 8 PM)
4. **Weekly** - Sundays at 2 AM
5. **Custom** - Define your own cron schedule

### Retention Policy
- Backups older than 30 days are automatically deleted
- Maximum of 10 recent backups kept per category
- Weekly cleanup runs Mondays at 3 AM

## 📋 Monitoring Backups

### Check Backup Status
```bash
# List recent backups
ls -la backups/database/
ls -la backups/files/

# Check backup sizes
du -sh backups/

# View backup logs
grep 'railway-backup' /var/log/system.log
```

### Cron Job Management
```bash
# View scheduled jobs
crontab -l

# Edit scheduled jobs
crontab -e

# Remove all scheduled jobs
crontab -r
```

## 🔧 Restore Procedures

### Database Restore
```bash
# Extract compressed backup
gunzip backups/database/textgather_db_backup_YYYYMMDD_HHMMSS.sql.gz

# Restore to local PostgreSQL
psql postgresql://username:password@localhost:5432/database_name < textgather_db_backup_YYYYMMDD_HHMMSS.sql

# Or restore via Railway
railway shell -c "psql \$DATABASE_URL < /path/to/backup.sql"
```

### Files Restore
```bash
# Extract files backup
tar -xzf backups/files/textgather_files_YYYYMMDD_HHMMSS.tar.gz

# Files will be extracted to current directory
# Review contents before uploading to your service
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Railway CLI not found"**
```bash
brew install railway
railway login --browserless
```

**2. "Not linked to Railway project"**
```bash
railway link
# Select your project from the list
```

**3. "pg_dump command not found"**
- This means pg_dump is not available in your Railway container
- Try using Railway dashboard to export database manually
- Contact Railway support for PostgreSQL backup options

**4. "Permission denied"**
```bash
chmod +x backups/scripts/*.sh
```

**5. "Empty backup files"**
- Check your Railway service is running: `railway logs`
- Verify container names match your deployment
- Some files may not be accessible due to Railway's security model

### Testing Backups

Always test your backups before relying on them:

```bash
# Test database backup
./backups/scripts/backup_database.sh

# Verify backup file exists and has content
ls -la backups/database/
zcat backups/database/latest_backup.sql.gz | head -20

# Test files backup
./backups/scripts/backup_files.sh

# Verify backup contents
tar -tzf backups/files/latest_backup.tar.gz | head -20
```

## 📞 Support

- **Railway Documentation**: https://docs.railway.app/
- **Railway CLI Help**: `railway --help`
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

## 🔒 Security Notes

- Backup files contain sensitive data (database, uploaded files)
- Store backups securely and encrypt if needed
- Regularly rotate and test backup integrity
- Consider off-site backup storage for production environments
- Never commit backup files to version control

---

**Last Updated**: $(date)
**Backup System Version**: 1.0
**Compatible with**: Railway Multi-Container Services