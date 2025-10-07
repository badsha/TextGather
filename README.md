# VoiceScript Collector - Flask Application

## Overview

VoiceScript Collector is a web-based platform built with Flask for collecting high-quality voice and text data for NLP training. The system supports data providers, quality reviewers, and administrators with browser-based audio recording, multi-stage approval workflow, and flexible billing.

## Features

### Core Functionality
- **Multi-role Authentication**: Provider, Reviewer, and Admin roles
- **Audio Recording**: Browser-based voice recording with MediaRecorder API
- **Language Management**: Support for multiple languages with custom pricing
- **Quality Review System**: Multi-stage approval workflow with reviewer feedback
- **Billing System**: Automated payment calculation based on word count and duration
- **Analytics Dashboard**: Role-specific dashboards with comprehensive statistics

### Technical Architecture
- **Backend**: Flask (Python 3.8+)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Server-side rendered HTML with Tailwind CSS
- **Authentication**: Session-based with secure cookies
- **File Storage**: Local filesystem with secure upload handling

## Quick Start

### Prerequisites
- Python 3.8 or higher
- 50MB free disk space for audio files
- Modern web browser with microphone access

### Automated Deployment
1. Download or extract the project files to your desired location
2. Open terminal in the project directory
3. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
4. Start the application:
   ```bash
   ./start.sh
   ```

The application will be available at: http://localhost:8000

### Demo Accounts
All demo accounts use password: `demo123`

#### Core Demo Accounts
- **Admin**: `admin@demo.com` - Platform administrator  
- **Provider**: `provider@demo.com` - Standard data provider
- **Reviewer**: `reviewer@demo.com` - Quality reviewer

#### Additional Example Users
- **John Smith**: `john.provider@example.com` - Teen male provider
- **Maria Rodriguez**: `maria.provider@example.com` - Elderly female provider

#### Age & Gender Demo Users
**Male Providers:**
- **Alex Johnson**: `male.child@demo.com` - Child (0-12)
- **Ryan Davis**: `male.teen@demo.com` - Teen (13-19)  
- **Michael Brown**: `male.adult@demo.com` - Adult (20-59)
- **Robert Wilson**: `male.elderly@demo.com` - Elderly (60+)

**Female Providers:**
- **Emma Taylor**: `female.child@demo.com` - Child (0-12)
- **Sophie Anderson**: `female.teen@demo.com` - Teen (13-19)
- **Jessica Martinez**: `female.adult@demo.com` - Adult (20-59)
- **Margaret Garcia**: `female.elderly@demo.com` - Elderly (60+)

## Manual Installation

If you prefer manual setup:

### 1. Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-sqlalchemy python-dotenv werkzeug gunicorn

# Create uploads directory
mkdir -p uploads
chmod 755 uploads
```

### 2. Configuration
Create `.env` file (or copy from `.env.example`):
```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secure-random-secret-key
DATABASE_URL=sqlite:///voicescript.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
```

### 3. Database Initialization
```bash
python3 -c "
from app import app, db, create_demo_data
with app.app_context():
    db.create_all()
    create_demo_data()
    print('Database initialized successfully')
"
```

### 4. Start Application
```bash
python app.py
```

## Production Deployment

### Using Gunicorn
```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

### Background Service (Linux)
The deployment script creates a systemd service file:
```bash
sudo cp voicescript-collector.service /etc/systemd/system/
sudo systemctl enable voicescript-collector
sudo systemctl start voicescript-collector
```

### Background Service (macOS)
Use screen for simple background operation:
```bash
screen -S voicescript
./start.sh
# Press Ctrl+A, then D to detach
# Reconnect with: screen -r voicescript
```

## Application Usage

### For Data Providers
1. Login with provider account
2. Browse available recording scripts
3. Record audio using browser microphone
4. Submit recordings with optional text notes
5. Track earnings and submission history

### For Quality Reviewers
1. Login with reviewer account
2. Access pending submissions queue
3. Review audio quality and content
4. Approve, reject, or request corrections
5. Track review earnings

### For Administrators
1. Login with admin account
2. Manage languages and pricing rates
3. Create and edit recording scripts
4. View platform analytics and user statistics
5. Monitor system performance

## File Structure

```
voicescript-collector/
├── app.py                 # Main Flask application
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── landing.html      # Landing page
│   ├── dashboard_*.html  # Role-specific dashboards
│   ├── record.html       # Audio recording interface
│   └── admin_*.html      # Admin management pages
├── uploads/              # Audio file storage
├── voicescript.db        # SQLite database (created automatically)
├── deploy.sh             # Automated deployment script
├── start.sh              # Application startup script
├── .env                  # Environment configuration
└── *.md                  # Documentation files
```

## Security Features

- **Session Management**: Secure HTTP-only cookies with CSRF protection
- **File Upload Security**: Type validation and size limits (50MB)
- **Role-Based Access**: Strict permission controls for different user types
- **Input Sanitization**: Protection against common web vulnerabilities
- **Database Security**: SQLAlchemy ORM prevents SQL injection

## Network Configuration

### Local Network Access
To access from other devices on your network:

1. Find your machine's IP address:
   ```bash
   # Linux/macOS
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig | findstr "IPv4"
   ```

2. The application binds to `0.0.0.0:8000` by default, so it's accessible from:
   - Local: `http://localhost:8000`
   - Network: `http://[YOUR_IP]:8000`

### Port Configuration
The application uses port 8000 by default (avoiding macOS AirPlay conflicts). To change:
- Set `PORT=9000` in your `.env` file
- Or modify `app.py` directly

## Troubleshooting

### Common Issues

**Microphone not working**
- Ensure browser has microphone permissions
- Use Chrome or Firefox (Safari may have limitations)
- Check that you're using `http://localhost:8000` not `127.0.0.1:8000`

**Database errors**
- Delete `voicescript.db` and run deployment script again
- Check file permissions in project directory

**Port already in use**
- Change port in `.env` file: `PORT=9000`
- Or kill existing process: `lsof -ti:8000 | xargs kill -9`

**Audio files not playing**
- Check uploads directory permissions: `chmod -R 755 uploads/`
- Verify audio files exist in uploads directory

### Performance Optimization
- Use Gunicorn with multiple workers for production
- Monitor disk space for audio file accumulation
- Consider PostgreSQL for high-traffic deployments
- Set up nginx reverse proxy for better static file serving

## Backup and Maintenance

### Important Data
```bash
# Backup database
cp voicescript.db voicescript.db.backup

# Backup audio files
tar -czf uploads_backup.tar.gz uploads/

# Backup configuration
cp .env .env.backup
```

### Clean Installation
```bash
# Stop application (Ctrl+C)
rm -rf venv/ voicescript.db uploads/
./deploy.sh  # Redeploy from scratch
```

## System Requirements

### Minimum Requirements
- CPU: 1 core, 1GHz
- RAM: 512MB available
- Storage: 1GB free space
- Network: Standard internet connection

### Recommended for Production
- CPU: 2+ cores
- RAM: 2GB+ available
- Storage: 10GB+ free space (for audio files)
- SSD storage for better performance

### Browser Compatibility
- Chrome 60+ (recommended)
- Firefox 55+
- Safari 12+ (limited microphone support)
- Edge 79+

## Development

### Adding New Features
1. Modify `app.py` for backend logic
2. Update templates in `templates/` directory
3. Add database models using SQLAlchemy
4. Test with demo accounts
5. Update documentation

### Database Schema Changes
The application uses SQLAlchemy with automatic table creation. Schema changes are applied automatically when the application starts.

## License

MIT License - see LICENSE file for details.

## Support

For issues or questions:
1. Check this README and deployment guides
2. Review console logs for error messages
3. Verify all prerequisites are installed
4. Try rerunning the deployment script

---

**Note**: This is a Flask-based Python application with server-side rendering. No Node.js, npm, or React components are required.