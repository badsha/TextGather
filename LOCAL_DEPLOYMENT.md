# Local Mac Mini Deployment Instructions

## Step-by-Step Setup for Mac Mini

### 1. Prepare Your Mac Mini
Ensure your Mac Mini has:
- macOS 10.15+ (Catalina or newer)
- Python 3.8+ (check with `python3 --version`)
- At least 1GB free space
- Terminal access

### 2. Download the Project
```bash
# If you have the project files, navigate to the directory
cd /path/to/voicescript-collector

# Or if downloading, extract to desired location
# Make sure all project files are present
```

### 3. Run Automated Setup
```bash
# Make deployment script executable (if needed)
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The script will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up database with demo data
- ✅ Create startup scripts
- ✅ Configure security settings

### 4. Start the Application
```bash
# Start the server
./start.sh
```

You'll see:
```
🚀 Starting VoiceScript Collector...
📊 Dashboard will be available at: http://localhost:8000
👤 Demo Accounts:
   Provider: provider@demo.com / demo123
   Reviewer: reviewer@demo.com / demo123
   Admin:    admin@demo.com / demo123

Press Ctrl+C to stop the server
```

### 5. Access the Application
1. Open your web browser
2. Go to: http://localhost:8000
3. Login with any demo account
4. Start using the platform!

## Network Access (Optional)

### Access from Other Devices
To access from other devices on your network:

1. Find your Mac Mini's IP address:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Edit `app.py` to bind to all interfaces:
   ```python
   app.run(host='0.0.0.0', port=8000, debug=True)
   ```

3. Access from other devices using: `http://[MAC_MINI_IP]:8000`

### Firewall Configuration
If needed, allow port 8000 through macOS firewall:
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Add Python or your application to allowed apps

## Production Setup

### Run as Background Service
For always-on operation:

1. **Using screen (simple)**:
   ```bash
   screen -S voicescript
   ./start.sh
   # Press Ctrl+A, then D to detach
   # Reconnect with: screen -r voicescript
   ```

2. **Using launchd (macOS service)**:
   Create `/Library/LaunchDaemons/com.voicescript.collector.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.voicescript.collector</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/your/project/start.sh</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
   </dict>
   </plist>
   ```

   Then:
   ```bash
   sudo launchctl load /Library/LaunchDaemons/com.voicescript.collector.plist
   ```

## Data Management

### Backup Important Data
```bash
# Backup database
cp voicescript.db voicescript.db.backup

# Backup audio files
tar -czf uploads_backup.tar.gz uploads/

# Backup configuration
cp .env .env.backup
```

### Reset/Clean Install
```bash
# Stop the application (Ctrl+C)
# Remove virtual environment
rm -rf venv/
# Remove database
rm voicescript.db
# Remove uploads
rm -rf uploads/
# Run deployment again
./deploy.sh
```

## Monitoring & Maintenance

### Check Application Status
```bash
# If running in background, check process
ps aux | grep python | grep app.py

# Check log files (if using systemd/launchd)
tail -f /var/log/system.log | grep voicescript
```

### Update Application
```bash
# Stop current application
# Replace files with new version
# Run deployment script again
./deploy.sh
./start.sh
```

### Disk Space Management
Audio files will accumulate over time:
```bash
# Check uploads directory size
du -sh uploads/

# Clean old files if needed (be careful!)
find uploads/ -name "*.mp4" -mtime +30 -delete
```

## Troubleshooting Mac-Specific Issues

### Python Issues
```bash
# If python3 command not found
brew install python3

# If pip issues
python3 -m ensurepip --upgrade
```

### Permission Issues
```bash
# Fix permissions
chmod -R 755 .
chmod +x deploy.sh start.sh
```

### Port Issues
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
kill -9 [PID]
```

### Browser Microphone Issues
- Safari: Preferences → Websites → Microphone → Allow
- Chrome: Settings → Privacy and Security → Site Settings → Microphone
- Ensure using `http://localhost:8000` not `127.0.0.1:8000`

## Performance on Mac Mini

### Optimizations
- Mac Mini can easily handle 10+ concurrent users
- SQLite is sufficient for up to 1000 users
- Audio files: ~300KB per minute of recording
- RAM usage: ~50MB for the application

### Scaling Considerations
- For 100+ concurrent users, consider PostgreSQL
- For heavy audio processing, monitor disk I/O
- Use SSD storage for better performance