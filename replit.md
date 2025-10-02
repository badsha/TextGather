# VoiceScript Collector - NLP Data Collection Platform

## Overview

VoiceScript Collector is a web-based platform designed to collect high-quality voice and text data for NLP training. The system supports a structured workflow involving data providers (who submit voice/text data), quality reviewers (who verify submissions), and administrators (who manage the platform). Built with a modern full-stack architecture using React, Express, and PostgreSQL.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture (Python Flask)
- **Runtime**: Python 3.11 with Flask framework
- **Template Engine**: Jinja2 for server-side rendering with Tailwind CSS
- **Database ORM**: SQLAlchemy with SQLite (development) / PostgreSQL (production)
- **Authentication**: Session-based authentication with Google OAuth integration
- **Session Management**: Flask sessions with secure cookie configuration
- **File Uploads**: Werkzeug secure file handling with validation
- **Production Server**: Gunicorn WSGI server with multi-worker support

### Database Design
- **Primary Database**: SQLite (local development) / PostgreSQL (production)
- **Schema Management**: SQLAlchemy automatic table creation with model definitions
- **Key Tables**:
  - `users`: User profiles with role-based access (provider/reviewer/admin)
  - `scripts`: Pre-defined prompts for voice recording
  - `submissions`: User-generated content (audio/text/combined)
  - `reviews`: Quality assessments of submissions
  - `billing_records`: Payment tracking for approved submissions
  - `sessions`: Authentication session storage

## Key Components

### Authentication System
- **Provider**: Local authentication with session management
- **Session Storage**: In-memory sessions (configurable for PostgreSQL in production)
- **Authorization**: Role-based access control (provider, reviewer, admin)
- **Security**: Secure cookies with HTTP-only flags
- **Demo Users**: Three test accounts for development (provider, reviewer, admin)
- **Production**: Real user registration and email/password authentication

### Data Collection Workflow
1. **Admin Script Creation**: Administrators create recording scripts with prompts
2. **Script Selection**: Users browse and select from available scripts
3. **Voice Recording**: Users provide audio recordings (required) with optional text notes
4. **Multi-Voice Collection**: Support for different voice types (men, women, children) per script
5. **Quality Review**: Reviewers assess audio submissions for approval
6. **Billing Integration**: Automatic payment calculation for approved recordings

### File Management
- **Audio Storage**: Local filesystem with Multer handling
- **File Validation**: Audio file type and size restrictions (50MB limit)
- **Security**: Controlled file access through API endpoints

### UI Components
- **Audio Recorder**: Custom component with MediaRecorder API integration
- **Review Interface**: Comprehensive review tools with quality scoring
- **Dashboard**: Role-specific views with statistics and recent activity
- **Navigation**: Responsive navigation with role-based menu items

### Mobile-First Responsive Design
- **Hamburger Navigation**: Mobile menu with smooth animations and ARIA support
  - ESC key and outside-click to close
  - Auto-closes on navigation
  - 44px minimum touch targets
- **Responsive Tables**: Mobile card view and desktop table layout
  - Provider dashboard submissions show as cards on mobile
  - Full table view on tablets and desktops (768px+)
- **Touch-Optimized UI**: Proper spacing and button sizes for mobile devices
- **Error Pages**: Mobile-friendly 404, 403, and 500 error pages
- **Viewport Configuration**: Proper meta tags for mobile scaling and accessibility

## Data Flow

### Submission Process
1. User authenticates via Replit Auth
2. User selects script or creates custom content
3. Audio recording captured via WebRTC MediaRecorder
4. Form data and audio file uploaded via multipart/form-data
5. Submission stored in database with pending status
6. Real-time UI updates via React Query cache invalidation

### Review Process
1. Reviewers access pending submissions queue
2. Audio playback and content review interface
3. Quality scoring and feedback submission
4. Status updates (approved/rejected/correction requested)
5. Billing record creation for approved submissions

### Analytics and Reporting
- User statistics (submission counts, earnings)
- Platform metrics (approval rates, content volume)
- Real-time dashboard updates

## External Dependencies

### Core Dependencies
- **Flask**: Web framework for Python
- **Flask-SQLAlchemy**: Database ORM integration
- **python-dotenv**: Environment variable management
- **Werkzeug**: WSGI utility library for file uploads
- **Gunicorn**: Production WSGI server

### Frontend Styling
- **Tailwind CSS**: Utility-first CSS framework (via CDN)
- **Font Awesome**: Icon library (via CDN)
- **MediaRecorder API**: Browser-based audio recording

### Authentication
- **Flask Sessions**: Built-in session management with secure cookies
- **SQLAlchemy**: Database models for user management

## Deployment Strategy

### Development Environment
- **Dev Server**: Vite dev server with HMR for frontend
- **Backend**: tsx for TypeScript execution with live reload
- **Database**: Neon PostgreSQL with development branch
- **File Storage**: Local filesystem for audio uploads

### Production Build
- **Frontend**: Vite production build with asset optimization
- **Backend**: ESBuild bundling to single JavaScript file
- **Database**: Neon PostgreSQL production instance
- **Static Assets**: Served via Express static middleware

### Environment Configuration
- Database URL configuration via environment variables
- Session secrets and authentication credentials
- File upload directory configuration
- Development vs production feature flags

### Scalability Considerations
- Database connection pooling via Neon serverless
- React Query caching reduces API calls
- Optimistic UI updates for better user experience
- Role-based route protection and data access

## Local Deployment Configuration

### Production Build System
- **Frontend Build**: Vite production build with asset optimization
- **Backend Build**: ESBuild bundling for Node.js deployment
- **Static Assets**: Express static middleware serves built frontend
- **Process Management**: PM2 configuration for production deployment

### Deployment Files
- **README.md**: Comprehensive deployment guide with step-by-step instructions
- **DEPLOYMENT_GUIDE.md**: Quick start guide for local deployment
- **deploy.sh**: Automated deployment script with environment setup
- **.env.example**: Template for environment configuration
- **ecosystem.config.js**: PM2 configuration for process management
- **docker-compose.yml**: PostgreSQL database setup via Docker
- **Dockerfile**: Full application containerization (optional)
- **healthcheck.js**: Application health monitoring endpoint

### Local Machine Requirements
- Node.js 18+ for modern JavaScript features
- PostgreSQL 13+ for database operations
- Proper file permissions for upload directory
- Environment variables for database and session configuration

### Security Features
- Secure session management with configurable secrets
- Database connection encryption
- File upload restrictions and validation
- Health check endpoint for monitoring
- Production-ready error handling

### Authentication System (Local)
- Token-based authentication with local session storage
- Demo user accounts for immediate testing
- Role-based access control (admin, reviewer, provider)
- Secure password handling and session management

### Recent Changes (Latest - October 1, 2025)
- ✅ **REAL-TIME TRANSCRIPTION**: Live speech-to-text display during recording
  - Web Speech API integration for real-time transcription
  - Transcript appears as users speak with visual feedback
  - Final text displayed in black, interim text in gray
  - Auto-restarts if connection drops during recording
  - Supports Chrome/Edge browsers (built-in Web Speech API)
  - Helps users verify recording clarity and accuracy
- ✅ **CASCADE DELETE SYSTEM**: Script deletion now removes all related recordings
  - Deleting a script automatically deletes all associated submissions
  - Audio files are removed from filesystem when submissions are deleted
  - Works for both single script delete and bulk delete operations
  - Provides feedback on number of submissions and files deleted
- ✅ **ADMIN RECORDING DELETE**: Admins can delete individual recordings
  - Delete button added to data export page for each recording
  - Removes submission record and associated audio file
  - Confirmation dialog prevents accidental deletions
  - DELETE endpoint: `/api/submissions/<id>`
- ✅ **DATA EXPORT SYSTEM**: Comprehensive data export functionality for ML training workflows
  - New `/admin/data-export` page showing all recordings in sortable table
  - CSV metadata export with complete recording information
  - Statistics dashboard (total, approved, field-collected, user-submitted counts)
  - Supports both field-collected and user-submitted recordings
  - Export format: ID, Audio Filename, Script Content, Language, Demographics, Status, Timestamps
  - Accessible via "Export" link in admin navigation (desktop + mobile)
  
### Previous Changes (September 30, 2025)
- ✅ **FIELD COLLECTION AUTO-APPROVAL**: Admin field-collected recordings now auto-approve
  - Field-collected submissions set to 'approved' status automatically
  - Skip review queue for trusted admin-collected data
  - Maintains quality workflow for user submissions
- ✅ **SCRIPT SUBMISSIONS VIEWER**: Added comprehensive submissions tracking per script
  - "View Submissions" button on admin scripts page
  - Modal displays all recordings for each script (regular + field-collected)
  - Shows submitter info, speaker metadata, status, and audio playback
  - Distinguishes between user submissions and field-collected data
- ✅ **MOBILE-FIRST RESPONSIVE DESIGN**: Implemented comprehensive mobile UI improvements
  - Added hamburger navigation menu with ARIA accessibility support
  - Implemented responsive table/card layouts (mobile cards, desktop tables)
  - Added ESC key and outside-click to close mobile menu
  - Created mobile-friendly error pages (404, 403, 500)
  - Touch-optimized UI with 44px minimum touch targets
  - Tested and verified across mobile (375px), tablet (768px), and desktop (1280px) viewports
- ✅ **DOCKER SESSION FIX**: Fixed login redirect issue in Docker deployments
  - Added USE_HTTPS environment variable to control secure cookie behavior
  - Docker (HTTP) now works with USE_HTTPS=false
  - HTTPS deployments can set USE_HTTPS=true for secure cookies
- ✅ **SECURITY HARDENING**: Disabled fallback authentication in production
  - Added ENABLE_WEBVIEW_FALLBACK flag (default: false)
  - Fallback cookie/token auth only available in development mode
  - Prevents privilege escalation via forged cookies in production
- ✅ **COMPREHENSIVE DOCKER DOCUMENTATION**: Created DOCKER.md deployment guide
  - Session configuration troubleshooting
  - HTTPS reverse proxy setup guidance
  - Security best practices for production
  
### Previous Changes (August 11, 2025)
- ✅ **WORKFLOW DEBUGGING FIXED**: Resolved npm run dev failure by creating minimal package.json wrapper
- ✅ **CODEBASE CLEANUP**: Removed unnecessary JavaScript/TypeScript files (client/, server/, shared/, config files)  
- ✅ **PURE PYTHON ARCHITECTURE**: Restored clean Flask-only codebase without Node.js dependencies
- ✅ **MINIMAL NODE SETUP**: Created simple package.json that runs Python Flask app via npm run dev
- ✅ **APPLICATION STATUS**: Python Flask application running successfully on port 8000 with all features
- → **STATUS**: Clean Python Flask application with minimal Node.js wrapper for workflow compatibility

### Authentication Test Results - CONFIRMED WORKING
- Test Client: ✅ Login 302 → Dashboard 200 (Working)
- Session Data: ✅ {'user_id': 1, 'user_role': 'provider', 'user_name': 'Demo Provider'}  
- Curl Tests: ✅ Login 302 → Dashboard 200 (Working)
- Debug Output: ✅ Session properly stored and retrieved in Replit environment
- **AUTHENTICATION SYSTEM CONFIRMED WORKING**: Session-based authentication working perfectly in local environment
- **GOOGLE OAUTH ROUTES ADDED**: Complete Google login functionality with account linking and profile picture support
- **PRODUCTION READY**: All core features implemented - recording, review workflow, billing, admin panel, multi-language support
- **DEPLOYMENT READY**: Local deployment package complete with comprehensive documentation and setup scripts
- **NOTE**: Replit webview has iframe session limitations (known issue) - application works perfectly when deployed locally