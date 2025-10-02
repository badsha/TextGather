#!/bin/bash

# VoiceScript Collector - Local Deployment Script
# This script sets up the application on your local machine

set -e  # Exit on any error

echo "🚀 VoiceScript Collector - Local Deployment"
echo "============================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and run this script again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📋 Installing Python dependencies..."
pip install flask flask-sqlalchemy python-dotenv werkzeug gunicorn authlib requests

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

# Set permissions for uploads directory
chmod 755 uploads

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env configuration file..."
    cat > .env << EOF
# VoiceScript Collector Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:///voicescript.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800

# Google OAuth Configuration (optional - uncomment and configure to enable)
# GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-google-client-secret
EOF
    echo "✅ .env file created with secure random secret key"
else
    echo "✅ .env file already exists"
fi

# Create systemd service file (optional)
echo "🔧 Creating systemd service file..."
cat > voicescript-collector.service << EOF
[Unit]
Description=VoiceScript Collector
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create startup script
echo "📝 Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
# VoiceScript Collector Startup Script

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "🚀 Starting VoiceScript Collector..."
echo "📊 Dashboard will be available at: http://localhost:8000"
echo "👤 Demo Accounts:"
echo "   Provider: provider@demo.com / demo123"
echo "   Reviewer: reviewer@demo.com / demo123"
echo "   Admin:    admin@demo.com / demo123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python app.py
EOF

# Make scripts executable
chmod +x start.sh
chmod +x deploy.sh

# Initialize database and create demo data
echo "🗄️  Initializing database..."
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python3 -c "
from app import app, db, create_demo_data
with app.app_context():
    db.create_all()
    create_demo_data()
    print('✅ Database initialized with demo data')
"

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "The application will be available at: http://localhost:8000"
echo ""
echo "Demo Accounts:"
echo "  Provider: provider@demo.com / demo123"
echo "  Reviewer: reviewer@demo.com / demo123"
echo "  Admin:    admin@demo.com / demo123"
echo ""
echo "For production deployment with systemd:"
echo "  sudo cp voicescript-collector.service /etc/systemd/system/"
echo "  sudo systemctl enable voicescript-collector"
echo "  sudo systemctl start voicescript-collector"