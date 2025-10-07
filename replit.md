# VoiceScript Collector - NLP Data Collection Platform

## Overview
VoiceScript Collector is a web-based platform for collecting high-quality voice and text data crucial for NLP training. It facilitates a structured workflow among data providers, quality reviewers, and administrators. The platform aims to streamline data acquisition for machine learning models, ensuring high quality and efficient processing of linguistic data.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Backend
The backend is built with Python 3.11 using the Flask framework. It utilizes Jinja2 for server-side rendering and SQLAlchemy for ORM, connecting to SQLite for development and PostgreSQL for production. Authentication is session-based, including Google OAuth integration, with secure cookie management. Gunicorn serves the application in production.

**Code Organization:**
- **app.py** (2259 lines): Main Flask app with configuration, routes, and business logic
- **models.py** (133 lines): SQLAlchemy database models (User, Script, Submission, etc.)
- **utils.py** (104 lines): Helper functions and decorators (require_auth, require_role, etc.)

### Database Design
The system uses SQLite (development) and PostgreSQL (production). Key tables include `users` (with role-based access), `scripts` (recording prompts), `submissions` (user-generated content), `reviews` (quality assessments), `billing_records`, and `sessions`.

### Database Migration System (Flyway-style)
The platform uses a **database-first migration workflow** where SQL scripts drive schema changes. The app **does NOT use db.create_all()** - all schema management is handled by SQL migrations.

**Local Docker Workflow:**
1. Write SQL migration scripts in `db/migrations/` with sequential naming: `V001__description.sql`, `V002__description.sql`, etc.
2. Update Python models in `models.py` to match the database schema
3. Run: `docker-compose -f docker-compose-secure.yml up --build`
4. Migrations run automatically via `docker-entrypoint.sh`

**Production Workflow (Railway):**
1. Create new SQL file: `db/migrations/V00X__your_change.sql`
2. Write SQL (e.g., `ALTER TABLE users ADD COLUMN phone VARCHAR(20);`)
3. Update models in `models.py` to reflect changes
4. Commit and push to GitHub → Railway automatically runs migrations via `docker-entrypoint.sh`

**Direct Python (Development):**
1. Run: `python run.py` (uses hybrid approach: migrations or SQLAlchemy fallback)

**Key Features:**
- **Pure Database-First**: No `db.create_all()` - schema managed exclusively by SQL migrations
- Sequential execution based on version numbers
- Checksum validation prevents modification of applied migrations
- Transactional execution with automatic rollback on errors
- Execution time tracking for performance monitoring
- Migration tracking in `schema_version` table

### Data Collection Workflow
1. **Admin Script Creation**: Administrators create recording scripts.
2. **Script Selection**: Users choose from available scripts.
3. **Voice Recording**: Users submit audio recordings (required) with optional text notes.
4. **Multi-Voice Collection**: Supports various voice types per script.
5. **Quality Review**: Reviewers assess submissions.
6. **Billing Integration**: Automatic payment calculation for approved recordings.

### File Management
Audio files are stored on the local filesystem and handled securely with validation for type and size (50MB limit).

### UI/UX
The platform features a custom audio recorder, a comprehensive review interface, role-specific dashboards, and responsive navigation. It is designed with a mobile-first approach, including hamburger navigation, responsive tables, and touch-optimized UI.

### Key Features
- **Authentication**: Local and Google OAuth with role-based access control (provider, reviewer, admin).
- **Real-Time Transcription**: Live speech-to-text during recording (Chrome/Edge), with transcripts saved to the database.
- **Admin Functionality**: View all submissions per script, inline audio playback and deletion, cascade deletion for scripts, and comprehensive data export.
- **Field Collection Auto-Approval**: Submissions from field collection are automatically approved.
- **Security Hardening**: Disabled fallback authentication in production.

## External Dependencies

### Core
- **Flask**: Python web framework.
- **Flask-SQLAlchemy**: ORM for database interaction.
- **python-dotenv**: Environment variable management.
- **Werkzeug**: WSGI utility for file handling.
- **Gunicorn**: Production WSGI server.

### Frontend
- **Tailwind CSS**: Utility-first CSS framework.
- **Font Awesome**: Icon library.
- **MediaRecorder API**: Browser API for audio recording.

### Authentication
- **Flask Sessions**: Built-in session management.
- **SQLAlchemy**: User model management.

### Database
- **Neon PostgreSQL**: Production database service.