# VoiceScript Collector - Local Deployment Guide

## Quick Start

### Prerequisites
- Python 3.8 or higher
- 50MB free disk space for audio files
- Modern web browser with microphone access

### Automated Setup
1. Download or clone the project to your local machine
2. Open terminal in the project directory
3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```
4. Start the application:
   ```bash
   ./start.sh
   ```

The application will be available at: http://localhost:8000

## Demo Accounts
- **Provider**: `provider@demo.com` / `demo123`
- **Reviewer**: `reviewer@demo.com` / `demo123`  
- **Admin**: `admin@demo.com` / `demo123`

## Manual Setup (Alternative)

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
Create `.env` file:
```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
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

### Using Systemd (Linux)
1. Copy service file: `sudo cp voicescript-collector.service /etc/systemd/system/`
2. Enable service: `sudo systemctl enable voicescript-collector`
3. Start service: `sudo systemctl start voicescript-collector`

## Features Overview

### Data Providers
- Record audio content using browser microphone
- Submit text-based content
- View submission history and earnings
- Track word count and payment calculations

### Quality Reviewers  
- Review pending submissions
- Rate content quality (1-5 stars)
- Approve, reject, or request changes
- Track review earnings (fixed rate per review)

### Administrators
- Manage languages and pricing rates
- Create and edit recording scripts
- View platform analytics
- Manage user accounts and roles

## Technical Architecture

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite (local) / PostgreSQL (production)
- **Authentication**: Session-based with secure cookies
- **File Storage**: Local filesystem with secure upload handling

### Frontend  
- **Styling**: Tailwind CSS
- **Icons**: Font Awesome
- **Audio**: MediaRecorder API (WebRTC)
- **Forms**: HTML5 with JavaScript validation

### Key Components
- Multi-role authentication system
- Language-specific pricing management
- Audio recording and playback
- Real-time billing calculations
- Responsive dashboard interfaces

## Security Features
- Secure session management
- File upload validation and restrictions
- Role-based access control
- CSRF protection
- Input sanitization

## Troubleshooting

### Common Issues

**Microphone not working**
- Ensure browser has microphone permissions
- Use HTTPS in production for microphone access
- Check browser compatibility (Chrome/Firefox recommended)

**Database errors**
- Delete `voicescript.db` and run initialization again
- Check file permissions in project directory

**Port 8000 already in use**
- Change port in `app.py`: `app.run(host='0.0.0.0', port=9000)`
- Or kill existing process: `lsof -ti:8000 | xargs kill -9`

**Audio files not playing**
- Check uploads directory permissions: `chmod 755 uploads`
- Verify file paths in database match actual files

### Performance Optimization
- Use Gunicorn with multiple workers for production
- Configure nginx as reverse proxy for better performance
- Enable gzip compression for static assets
- Monitor disk space for audio file storage

## Support
For issues or questions:
1. Check this deployment guide
2. Review error logs in terminal
3. Verify all prerequisites are installed
4. Try rerunning the deployment script