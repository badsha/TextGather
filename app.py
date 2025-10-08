import os
import logging
import click
import uuid
import csv
import io
import zipfile
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, send_file, abort
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from datetime import datetime
from sqlalchemy import text

# Import database and models from models.py
from models import (
    db, User, Script, ScriptVariantRequirement, Submission,
    BillingRecord, Language, PricingRate, AppSettings
)

# Import utilities from utils.py
from utils import (
    get_app_setting, get_show_earnings, set_app_setting,
    require_auth, require_role, inject_common_variables
)

app = Flask(__name__)

# Production-ready configuration
is_production = os.environ.get('FLASK_ENV') == 'production'

# Secret key - fail fast in production if not set
if is_production and not os.environ.get('SECRET_KEY'):
    raise RuntimeError("SECRET_KEY environment variable must be set in production")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration - PostgreSQL first, SQLite only for local development
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    if is_production:
        raise RuntimeError("DATABASE_URL environment variable must be set in production")
    else:
        # Local development fallback to SQLite
        database_url = 'sqlite:///voicescript.db'
        app.logger.info("⚠️  Using SQLite for local development - use PostgreSQL for production")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Production security settings
# Auto-detect HTTPS for production or when explicitly set
# Railway, Heroku, and most cloud platforms run on HTTPS
use_https = (
    os.environ.get('USE_HTTPS', 'false').lower() == 'true' or  # Explicit override
    is_production or  # Enable secure cookies in production by default
    'railway.app' in os.environ.get('RAILWAY_STATIC_URL', '') or  # Railway detection
    'herokuapp.com' in os.environ.get('HEROKU_APP_NAME', '')  # Heroku detection
)
app.config['PREFERRED_URL_SCHEME'] = 'https' if use_https else 'http'
app.config['SESSION_COOKIE_SECURE'] = use_https  # Only secure on HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['WTF_CSRF_ENABLED'] = is_production

# Enhanced database configuration for PostgreSQL connection stability
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,      # Test connections before use to catch dropped connections
    'pool_recycle': 300,        # Recycle connections every 5 minutes
    'pool_timeout': 20,         # Timeout for getting connection from pool
    'pool_size': 5,             # Number of connections to keep open
    'max_overflow': 10,         # Additional connections if pool is full
    'echo': False               # Set to True for SQL debugging if needed
}
app.config['UPLOAD_FOLDER'] = 'uploads'

# Session configuration - production vs development
if is_production:
    # Production session settings
    app.config['SESSION_COOKIE_NAME'] = 'voicescript_session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
else:
    # Development session settings for Replit environment
    app.config['SESSION_COOKIE_NAME'] = 'voicescript_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# Ensure required directories exist FIRST (before logging)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
if is_production:
    os.makedirs('logs', exist_ok=True)

# Production logging configuration
if is_production:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info('VoiceScript Collector startup - Production Mode')
else:
    logging.basicConfig(level=logging.DEBUG)
    app.logger.info('VoiceScript Collector startup - Development Mode')

# Initialize database with app
db.init_app(app)

oauth = OAuth(app)

# Configure Google OAuth only if credentials are available
google = None
if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']:
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# Register context processor
app.context_processor(inject_common_variables)

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('landing.html')

    user_role = session['user_role']
    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif user_role == 'reviewer':
        return redirect(url_for('reviewer_dashboard'))
    else:
        return redirect(url_for('provider_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        user_role = session.get('user_role', 'provider')
        if user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user_role == 'reviewer':
            return redirect(url_for('reviewer_dashboard'))
        else:
            return redirect(url_for('provider_dashboard'))
    
    # Handle demo login via URL parameter
    demo_role = request.args.get('demo')
    if demo_role in ['provider', 'reviewer', 'admin']:
        email = f"{demo_role}@demo.com"
        user = User.query.filter_by(email=email).first()
        if user:
            # Store user info in the session with explicit permanence
            session.clear()  # Clear any old session data
            session.permanent = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session.modified = True
            
            app.logger.info(f"Demo login: {email} -> {user.role} (ID: {user.id})")
            flash('Login successful!', 'success')

            # Create response and redirect to appropriate dashboard
            if user.role == 'admin':
                response = redirect(url_for('admin_dashboard'))
            elif user.role == 'reviewer':
                response = redirect(url_for('reviewer_dashboard'))
            else:
                response = redirect(url_for('provider_dashboard'))
            
            # Only set fallback cookie in development mode with explicit flag (SECURITY)
            enable_fallback = os.environ.get('ENABLE_WEBVIEW_FALLBACK', 'false').lower() == 'true'
            if enable_fallback and not is_production:
                response.set_cookie('voicescript_session', 
                                  value=f"{user.id}:{user.role}:{user.first_name} {user.last_name}",
                                  max_age=3600,
                                  secure=False,
                                  httponly=False,
                                  samesite='Lax',
                                  path='/')
            return response

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Store user info in the session with explicit permanence
            session.clear()  # Clear any old session data
            session.permanent = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session.modified = True
            
            app.logger.info(f"User login: {email} -> {user.role} (ID: {user.id})")
            flash('Login successful!', 'success')

            # Create response and redirect to appropriate dashboard
            if user.role == 'admin':
                response = redirect(url_for('admin_dashboard'))
            elif user.role == 'reviewer':
                response = redirect(url_for('reviewer_dashboard'))
            else:
                response = redirect(url_for('provider_dashboard'))
            
            # Only set fallback cookie in development mode with explicit flag (SECURITY)
            enable_fallback = os.environ.get('ENABLE_WEBVIEW_FALLBACK', 'false').lower() == 'true'
            if enable_fallback and not is_production:
                response.set_cookie('voicescript_session', 
                                  value=f"{user.id}:{user.role}:{user.first_name} {user.last_name}",
                                  max_age=3600,
                                  secure=False,
                                  httponly=False,
                                  samesite='Lax',
                                  path='/')
            return response
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

# Google OAuth routes
@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    if not google or not app.config['GOOGLE_CLIENT_ID']:
        flash('Google authentication is not configured. Please use email/password login.', 'error')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback/google')
def google_callback():
    """Handle Google OAuth callback"""
    global logged_in_user
    
    if not google or not app.config['GOOGLE_CLIENT_ID']:
        flash('Google authentication is not configured.', 'error')
        return redirect(url_for('login'))
    
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            # Check if user exists
            user = User.query.filter_by(google_id=user_info['sub']).first()
            
            if not user:
                # Check if user with same email exists (local account)
                existing_user = User.query.filter_by(email=user_info['email']).first()
                if existing_user:
                    # Link Google account to existing local account
                    existing_user.google_id = user_info['sub']
                    existing_user.profile_picture = user_info.get('picture')
                    existing_user.auth_provider = 'google'
                    db.session.commit()
                    user = existing_user
                else:
                    # Create new user
                    user = User(
                        email=user_info['email'],
                        first_name=user_info.get('given_name', ''),
                        last_name=user_info.get('family_name', ''),
                        google_id=user_info['sub'],
                        profile_picture=user_info.get('picture'),
                        auth_provider='google',
                        role='provider'  # Default role for new Google users
                    )
                    db.session.add(user)
                    db.session.commit()
            
            # Store user info in the session with explicit permanence
            session.permanent = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            flash('Google login successful!', 'success')

            # Create response and redirect to appropriate dashboard
            if user.role == 'admin':
                response = redirect(url_for('admin_dashboard'))
            elif user.role == 'reviewer':
                response = redirect(url_for('reviewer_dashboard'))
            else:
                response = redirect(url_for('provider_dashboard'))
            
            # Only set fallback cookie in development mode with explicit flag (SECURITY)
            enable_fallback = os.environ.get('ENABLE_WEBVIEW_FALLBACK', 'false').lower() == 'true'
            if enable_fallback and not is_production:
                response.set_cookie('voicescript_session', 
                                  value=f"{user.id}:{user.role}:{user.first_name} {user.last_name}",
                                  max_age=3600,
                                  secure=False,
                                  httponly=False,
                                  samesite='Lax',
                                  path='/')
            return response
        else:
            flash('Failed to get user information from Google.', 'error')
            return redirect(url_for('login'))
                
    except Exception as e:
        flash(f'Google authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

# Webview authentication bypass route
@app.route('/webview_login')
def webview_login():
    """Direct authentication for Replit webview environment"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        user_role = session.get('user_role', 'provider')
        if user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user_role == 'reviewer':
            return redirect(url_for('reviewer_dashboard'))
        else:
            return redirect(url_for('provider_dashboard'))
    
    # Default to provider demo account for webview
    email = request.args.get('email', 'provider@demo.com')
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Store user info in the session
        session.clear()  # Clear any old session data
        session.permanent = True
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = f"{user.first_name} {user.last_name}"
        session.modified = True
        
        app.logger.info(f"Webview login: {email} -> {user.role} (ID: {user.id})")
        
        # Redirect to appropriate dashboard
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'reviewer':
            return redirect(url_for('reviewer_dashboard'))
        else:
            return redirect(url_for('provider_dashboard'))
    else:
        flash('Authentication failed', 'error')
        return redirect(url_for('login'))



@app.route('/dashboard/provider')
@require_auth  
def provider_dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
        
    submissions = Submission.query.filter_by(user_id=user.id).order_by(Submission.created_at.desc()).limit(10).all()
    scripts = Script.query.filter_by(is_active=True).all()
    
    # Calculate user stats
    total_submissions = Submission.query.filter_by(user_id=user.id).count()
    approved_submissions = Submission.query.filter_by(user_id=user.id, status='approved').count()
    pending_submissions = Submission.query.filter_by(user_id=user.id, status='pending').count()
    
    # Calculate earnings
    earnings = db.session.query(db.func.sum(BillingRecord.amount)).filter_by(user_id=user.id).scalar() or 0
    
    stats = {
        'total_submissions': total_submissions,
        'approved': approved_submissions,
        'pending': pending_submissions,
        'rejected': total_submissions - approved_submissions - pending_submissions,
        'earnings': round(earnings, 2)
    }
    
    return render_template('dashboard_provider.html', 
                         user=user, 
                         submissions=submissions, 
                         scripts=scripts, 
                         stats=stats)

@app.route('/dashboard/reviewer')
@require_role(['reviewer', 'admin'])
def reviewer_dashboard():
    pending_submissions = Submission.query.filter_by(status='pending').order_by(Submission.created_at.desc()).all()
    recent_reviews = Submission.query.filter(
        Submission.reviewed_by == session['user_id']
    ).order_by(Submission.reviewed_at.desc()).limit(10).all()
    
    return render_template('dashboard_reviewer.html', 
                         pending_submissions=pending_submissions, 
                         recent_reviews=recent_reviews)

# Admin convenience redirect
@app.route('/admin')
@require_role(['admin'])
def admin_redirect():
    """Redirect /admin to the main admin dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/dashboard/admin')
@require_role(['admin'])
def admin_dashboard():
    # Calculate platform stats
    stats = {
        'total_users': User.query.count(),
        'total_submissions': Submission.query.count(),
        'pending_submissions': Submission.query.filter_by(status='pending').count(),
        'approved_submissions': Submission.query.filter_by(status='approved').count(),
        'total_scripts': Script.query.count(),
        'active_scripts': Script.query.filter_by(is_active=True).count()
    }
    
    recent_activity = Submission.query.order_by(Submission.created_at.desc()).limit(10).all()
    
    return render_template('dashboard_admin.html', 
                         stats=stats, 
                         recent_activity=recent_activity)

# Additional routes for complete functionality  
@app.route('/record')
@require_auth
def record_list():
    # Scripts are now loaded via AJAX, no need to pass them
    return render_template('record.html')

@app.route('/record/script/<int:script_id>')
@require_auth
def record_script(script_id):
    language = request.args.get('language', 'en')
    # Handle script ID 0 as custom content creation
    if script_id == 0:
        script = None  # No script selected, custom content
    else:
        script = Script.query.get_or_404(script_id)
    
    scripts = Script.query.filter_by(is_active=True, language=language).order_by(Script.created_at.desc()).all()
    return render_template('record.html', script=script, scripts=scripts)

@app.route('/record-queue')
@require_auth
def record_queue():
    """Streamlined recording interface with auto-advance functionality"""
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Check if user has complete demographic profile
    if not user.gender or not user.age_group:
        flash('Please complete your profile with gender and age group information before recording.', 'error')
        return redirect(url_for('provider_dashboard'))
    
    # Get available languages
    languages = Language.query.filter_by(is_active=True).all()
    
    return render_template('record_queue.html', user=user, languages=languages)

# API endpoint to get paginated scripts data
@app.route('/api/scripts', methods=['GET'])
@require_auth
def get_scripts():
    # Get query parameters
    language = request.args.get('language', '')
    search_query = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(100, max(10, int(request.args.get('page_size', 20))))  # Cap at 100, min 10
    
    # Build query
    query = Script.query.filter_by(is_active=True)
    
    # Apply language filter if specified
    if language:
        query = query.filter(Script.language == language)
    
    # Apply search filter if specified
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Script.title.ilike(search_pattern),
                Script.content.ilike(search_pattern),
                Script.category.ilike(search_pattern)
            )
        )
    
    # Order and paginate
    query = query.order_by(Script.created_at.desc())
    total = query.count()
    scripts = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination info
    has_next = total > page * page_size
    
    return jsonify({
        'items': [{
            'id': script.id,
            'title': getattr(script, 'title', None) or f"Script {script.id}",
            'content': script.content[:200] + '...' if len(script.content) > 200 else script.content,  # Preview only
            'language': script.language,
            'category': getattr(script, 'category', None) or 'General',
            'difficulty': getattr(script, 'difficulty', None) or 'Medium',
            'target_duration': getattr(script, 'target_duration', None)
        } for script in scripts],
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_next': has_next
    })

# API endpoint to get individual script details for users
@app.route('/api/scripts/<int:script_id>/details', methods=['GET'])
@require_auth
def get_script_details(script_id):
    script = Script.query.filter_by(id=script_id, is_active=True).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    return jsonify({
        'id': script.id,
        'title': getattr(script, 'title', None) or f"Script {script.id}",
        'content': script.content,  # Full content
        'language': script.language,
        'category': getattr(script, 'category', None) or 'General',
        'difficulty': getattr(script, 'difficulty', None) or 'Medium',
        'target_duration': getattr(script, 'target_duration', None)
    })

# API endpoint to get available languages
@app.route('/api/languages', methods=['GET'])
@require_auth
def get_languages():
    languages = Language.query.filter_by(is_active=True).order_by(Language.name).all()
    return jsonify([{
        'code': lang.code,
        'name': lang.name,
        'native_name': lang.native_name
    } for lang in languages])

# Removed custom content route - only script-based recordings allowed

@app.route('/submissions')
@require_auth
def submissions():
    # Admins see ALL submissions, regular users see only their own
    if session.get('user_role') == 'admin':
        user_submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    else:
        user_submissions = Submission.query.filter_by(user_id=session['user_id']).order_by(Submission.created_at.desc()).all()
    return render_template('submissions.html', submissions=user_submissions)

@app.route('/submissions/<int:submission_id>/update-transcript', methods=['POST'])
@require_auth
def update_transcript(submission_id):
    """Update the transcript for a submission"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Check authorization: user can only edit their own submissions, unless admin
    if session.get('user_role') != 'admin' and submission.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.json or {}
    new_transcript = data.get('transcript', '').strip()
    
    try:
        submission.transcript = new_transcript if new_transcript else None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Transcript updated successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error updating transcript: {str(e)}')
        return jsonify({'success': False, 'error': 'Failed to update transcript'}), 500

@app.route('/reviews')
@require_role(['reviewer', 'admin'])
def reviews():
    pending_submissions = Submission.query.filter_by(status='pending').order_by(Submission.created_at.asc()).all()
    return render_template('reviews.html', submissions=pending_submissions)

@app.route('/admin/languages')
@require_role(['admin'])
def admin_languages():
    """Admin language and pricing management (merged interface)"""
    languages = Language.query.order_by(Language.created_at.desc()).all()
    
    # Get pricing data for all languages
    pricing_records = PricingRate.query.all()
    pricing_dict = {pricing.language_code: pricing for pricing in pricing_records}
    
    return render_template('admin_languages_pricing.html', 
                         languages=languages, 
                         pricing_dict=pricing_dict)

@app.route('/admin/scripts')
@require_role(['admin'])
def admin_scripts():
    scripts = Script.query.order_by(Script.created_at.desc()).all()
    languages = Language.query.all()
    return render_template('admin_scripts.html', scripts=scripts, languages=languages)

# Recording and submission routes
@app.route('/submit_recording', methods=['POST'])
@require_auth
def submit_recording():
    script_id = request.form.get('script_id')
    language_id = request.form.get('language_id')
    text_content = request.form.get('text_content', '').strip()
    transcript = request.form.get('transcript', '').strip()
    audio_file = request.files.get('audio_file')
    
    # Validate required fields - for script-based recordings, audio and language are mandatory
    if not script_id:
        return jsonify({'success': False, 'error': 'Script selection is required'}), 400
    
    if not language_id:
        return jsonify({'success': False, 'error': 'Language selection is required'}), 400
    
    if not audio_file or not audio_file.filename:
        return jsonify({'success': False, 'error': 'Audio recording is required for script submissions'}), 400
    
    # Handle audio file if uploaded
    audio_filename = None
    duration = None
    if audio_file and audio_file.filename:
        filename = secure_filename(audio_file.filename)
        # Generate unique filename to prevent conflicts
        audio_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure upload directory exists
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
        audio_file.save(os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), audio_filename))
    
    # Calculate word count - use script content if no text_content provided
    word_count = 0
    if text_content:
        word_count = len(text_content.split())
    elif script_id:
        # If recording from a script but no text provided, use script word count
        script = Script.query.get(int(script_id))
        if script and script.content:
            word_count = len(script.content.split())
    
    # Get user for demographic snapshot
    user = User.query.get(session['user_id'])
    
    # Create new submission with demographic snapshot
    try:
        submission = Submission(
            user_id=session['user_id'],
            script_id=int(script_id) if script_id and script_id != '0' else None,
            language_id=int(language_id),
            text_content=text_content,
            transcript=transcript if transcript else None,
            audio_filename=audio_filename,
            duration=duration,
            word_count=word_count,
            status='pending',
            provider_gender=user.gender if user else None,  # Snapshot at submission time
            provider_age_group=user.age_group if user else None  # Snapshot at submission time
        )
        
        db.session.add(submission)
        db.session.flush()  # Flush to get the ID before commit
        submission_id = submission.id
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Recording submitted successfully!', 'submission_id': submission_id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error submitting recording: {str(e)}')
        import traceback
        app.logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({'success': False, 'error': 'Failed to save recording. Please try again.'}), 500

# Field Collection Routes for Admins
@app.route('/admin/field-collect')
@require_role(['admin'])
def admin_field_collect():
    """Mobile-optimized field collection interface for admins"""
    languages = Language.query.filter_by(is_active=True).all()
    return render_template('admin_field_collect.html', languages=languages)

@app.route('/admin/field-collect/submit', methods=['POST'])
@require_role(['admin'])
def submit_field_collection():
    """Handle field-collected recording submissions by admins"""
    script_id = request.form.get('script_id')
    language_id = request.form.get('language_id')
    audio_file = request.files.get('audio_file')
    
    # Speaker metadata
    speaker_name = request.form.get('speaker_name', '').strip()
    speaker_location = request.form.get('speaker_location', '').strip()
    transcript = request.form.get('transcript', '').strip()
    transcript_language_id = request.form.get('transcript_language_id')  # Language of the transcript text
    provider_gender = request.form.get('provider_gender')
    provider_age_group = request.form.get('provider_age_group')
    
    # Validate required fields
    if not script_id:
        return jsonify({'success': False, 'message': 'Script selection is required'}), 400
    
    if not language_id:
        return jsonify({'success': False, 'message': 'Language selection is required'}), 400
    
    if not audio_file or not audio_file.filename:
        return jsonify({'success': False, 'message': 'Audio recording is required'}), 400
    
    if not provider_gender or not provider_age_group:
        return jsonify({'success': False, 'message': 'Speaker gender and age group are required'}), 400
    
    # Handle audio file upload
    filename = secure_filename(audio_file.filename)
    audio_filename = f"{uuid.uuid4()}_{filename}"
    
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    audio_file.save(os.path.join(upload_folder, audio_filename))
    
    # Calculate word count from script
    word_count = 0
    script = Script.query.get(int(script_id))
    if script and script.content:
        word_count = len(script.content.split())
    
    # Create field-collected submission (auto-approved, no review needed)
    submission = Submission(
        user_id=None,  # No user for field collections
        script_id=int(script_id),
        language_id=int(language_id),
        text_content='',
        transcript=transcript if transcript else None,
        transcript_language_id=int(transcript_language_id) if transcript_language_id else None,
        audio_filename=audio_filename,
        word_count=word_count,
        status='approved',  # Auto-approve field collections
        provider_gender=provider_gender,
        provider_age_group=provider_age_group,
        collected_by_admin_id=session['user_id'],  # Track who collected it
        speaker_name=speaker_name or None,
        speaker_location=speaker_location or None,
        is_field_collection=True
    )
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Recording submitted successfully!',
        'submission_id': submission.id
    })

# File serving route for audio files
@app.route('/uploads/<filename>')
@require_auth
def uploaded_file(filename):
    """Serve uploaded audio files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Delete submission route for providers
@app.route('/delete_submission/<int:submission_id>', methods=['POST'])
@require_auth
def delete_submission(submission_id):
    """Allow providers to delete their own submissions before review"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Check if user owns this submission
    if submission.user_id != session['user_id']:
        flash('You can only delete your own submissions.', 'error')
        return redirect(url_for('provider_dashboard'))
    
    # Check if submission is still pending (not reviewed)
    if submission.status != 'pending':
        flash('You can only delete submissions that haven\'t been reviewed yet.', 'error')
        return redirect(url_for('provider_dashboard'))
    
    # Delete audio file if it exists
    if submission.audio_filename:
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], submission.audio_filename)
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    # Delete submission from database
    db.session.delete(submission)
    db.session.commit()
    
    flash('Submission deleted successfully.', 'success')
    return redirect(url_for('provider_dashboard'))

# Review submission page for reviewers
@app.route('/review/submission/<int:submission_id>')
@require_role(['reviewer', 'admin'])
def review_submission(submission_id):
    """Display submission review interface"""
    submission = Submission.query.get_or_404(submission_id)
    return render_template('review_submission.html', submission=submission)

# API endpoint for processing review decisions
@app.route('/api/submissions/<int:submission_id>/review', methods=['POST'])
@require_role(['reviewer', 'admin'])
def process_review(submission_id):
    """Handle submission review by reviewers"""
    submission = Submission.query.get_or_404(submission_id)
    
    if request.method == 'GET':
        # Return submission details for review modal
        return jsonify({
            'id': submission.id,
            'script_title': submission.script.title if submission.script else 'Custom Content',
            'script_content': submission.script.content if submission.script else '',
            'text_content': submission.text_content or '',
            'audio_filename': submission.audio_filename,
            'word_count': submission.word_count,
            'duration': submission.duration,
            'created_at': submission.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': f"{submission.user.first_name} {submission.user.last_name}"
        })
    
    elif request.method == 'POST':
        # Process review decision
        data = request.json or {}
        action = data.get('action')  # 'approve', 'reject', or 'request_changes'
        review_notes = data.get('notes', '')
        quality_score = data.get('quality_score', 0)
        
        # Update submission
        submission.status = action if action in ['approved', 'rejected'] else 'pending'
        submission.reviewed_by = session['user_id']
        submission.reviewed_at = datetime.utcnow()
        submission.review_notes = review_notes
        submission.quality_score = quality_score
        
        # Create billing records for approved submissions
        if action == 'approved':
            # Get language-specific pricing
            script_language = submission.script.language if submission.script else 'en'
            pricing = PricingRate.query.filter_by(language_code=script_language).first()
            
            if not pricing:
                # Create default pricing if none exists
                pricing = PricingRate(
                    language_code=script_language,
                    provider_rate_per_word=0.01,
                    reviewer_rate_per_submission=2.00
                )
                db.session.add(pricing)
                db.session.flush()  # Get the ID
            
            # Provider payment (per word) - recalculate word count if needed
            provider_word_count = submission.word_count
            if provider_word_count == 0 and submission.script:
                # Use script word count if submission word count is 0
                provider_word_count = len(submission.script.content.split())
            
            if provider_word_count > 0:
                provider_amount = provider_word_count * pricing.provider_rate_per_word
                provider_billing = BillingRecord(
                    user_id=submission.user_id,
                    submission_id=submission.id,
                    amount=provider_amount,
                    rate_per_word=pricing.provider_rate_per_word,
                    billing_type='provider',
                    language_code=script_language,
                    word_count=provider_word_count
                )
                db.session.add(provider_billing)
            
            # Reviewer payment (per submission)
            reviewer_billing = BillingRecord(
                user_id=session['user_id'],  # Current reviewer
                submission_id=submission.id,
                amount=pricing.reviewer_rate_per_submission,
                rate_per_submission=pricing.reviewer_rate_per_submission,
                billing_type='reviewer',
                language_code=script_language
            )
            db.session.add(reviewer_billing)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Submission {action} successfully'
        })

# Pricing management routes
@app.route('/admin/pricing')
@require_role(['admin'])
def admin_pricing():
    """Admin interface for managing pricing rates"""
    languages = Language.query.filter_by(is_active=True).all()
    pricing_rates = PricingRate.query.all()
    
    # Create dict for easy lookup
    pricing_dict = {rate.language_code: rate for rate in pricing_rates}
    
    return render_template('admin_pricing.html', 
                         languages=languages, 
                         pricing_dict=pricing_dict)

@app.route('/api/pricing/update', methods=['POST'])
@require_role(['admin'])
def update_pricing():
    """Update pricing rates for languages"""
    data = request.json or {}
    language_code = data.get('language_code')
    provider_rate = float(data.get('provider_rate', 0.01))
    reviewer_rate = float(data.get('reviewer_rate', 2.00))
    currency = data.get('currency', 'USD')
    
    # Find or create pricing record
    pricing = PricingRate.query.filter_by(language_code=language_code).first()
    if pricing:
        pricing.provider_rate_per_word = provider_rate
        pricing.reviewer_rate_per_submission = reviewer_rate
        pricing.currency = currency
        pricing.updated_at = datetime.utcnow()
    else:
        pricing = PricingRate(
            language_code=language_code,
            provider_rate_per_word=provider_rate,
            reviewer_rate_per_submission=reviewer_rate,
            currency=currency
        )
        db.session.add(pricing)
    
    db.session.commit()
    return jsonify({'success': True})

# Earnings dashboard routes  
@app.route('/earnings')
@require_auth
def earnings_dashboard():
    """User earnings dashboard"""
    # Check if earnings functionality is enabled
    if not get_show_earnings():
        flash('Earnings functionality is currently disabled.', 'info')
        # Redirect to appropriate dashboard based on user role
        user_role = session.get('user_role', 'provider')
        if user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user_role == 'reviewer':
            return redirect(url_for('reviewer_dashboard'))
        else:
            return redirect(url_for('provider_dashboard'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's billing records (handle potential schema migration)
    try:
        provider_earnings = BillingRecord.query.filter_by(
            user_id=user_id, 
            billing_type='provider'
        ).order_by(BillingRecord.created_at.desc()).all()
        
        reviewer_earnings = BillingRecord.query.filter_by(
            user_id=user_id, 
            billing_type='reviewer'
        ).order_by(BillingRecord.created_at.desc()).all()
    except Exception as e:
        # Handle old schema - show empty for now
        provider_earnings = []
        reviewer_earnings = []
    
    # Calculate totals
    total_provider = sum(record.amount for record in provider_earnings)
    total_reviewer = sum(record.amount for record in reviewer_earnings)
    
    # Role-specific total earnings
    if user.role == 'provider':
        total_earnings = total_provider
    elif user.role == 'reviewer':
        total_earnings = total_reviewer
    else:  # admin
        total_earnings = total_provider + total_reviewer
    
    return render_template('earnings.html',
                         user=user,
                         provider_earnings=provider_earnings,
                         reviewer_earnings=reviewer_earnings,
                         total_provider=total_provider,
                         total_reviewer=total_reviewer,
                         total_earnings=total_earnings,
                         user_role=user.role)

# API routes for admin panel
@app.route('/api/scripts', methods=['POST'])
@require_role(['admin'])
def create_script():
    data = request.json or {}
    
    script = Script(
        content=data['content'],
        language=data.get('language', 'en')
    )
    db.session.add(script)
    db.session.commit()
    return jsonify({'success': True, 'id': script.id})

@app.route('/api/scripts/<int:script_id>', methods=['GET'])
@require_role(['admin'])
def get_script(script_id):
    script = Script.query.get_or_404(script_id)
    languages = Language.query.all()
    return jsonify({
        'success': True,
        'script': {
            'id': script.id,
            'content': script.content,
            'language': script.language,
            'is_active': script.is_active
        },
        'languages': [{'code': lang.code, 'name': lang.name} for lang in languages]
    })

@app.route('/api/scripts/<int:script_id>/submissions', methods=['GET'])
@require_role(['admin'])
def get_script_submissions(script_id):
    """Get all submissions for a specific script"""
    script = Script.query.get_or_404(script_id)
    
    submissions = Submission.query.filter_by(script_id=script_id).order_by(Submission.created_at.desc()).all()
    
    result = []
    for sub in submissions:
        # Get submitter info
        if sub.is_field_collection:
            admin = User.query.get(sub.collected_by_admin_id) if sub.collected_by_admin_id else None
            admin_name = f"{admin.first_name} {admin.last_name}" if admin else 'Unknown'
            submitter_name = f"Field: {sub.speaker_name or 'Anonymous'} (collected by {admin_name})"
        else:
            user = User.query.get(sub.user_id) if sub.user_id else None
            submitter_name = f"{user.first_name} {user.last_name}" if user else 'Unknown User'
        
        result.append({
            'id': sub.id,
            'submitter_name': submitter_name,
            'speaker_location': sub.speaker_location,
            'provider_gender': sub.provider_gender,
            'provider_age_group': sub.provider_age_group,
            'status': sub.status,
            'audio_filename': sub.audio_filename,
            'is_field_collection': sub.is_field_collection,
            'created_at': sub.created_at.strftime('%Y-%m-%d %H:%M') if sub.created_at else None
        })
    
    return jsonify({
        'success': True,
        'script': {
            'id': script.id,
            'content': script.content,
            'language': script.language
        },
        'submissions': result
    })

@app.route('/api/scripts/<int:script_id>', methods=['PUT'])
@require_role(['admin'])
def update_script(script_id):
    script = Script.query.get_or_404(script_id)
    data = request.json or {}
    
    script.content = data.get('content', script.content)
    script.language = data.get('language', script.language)
    script.is_active = data.get('is_active', script.is_active)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/scripts/<int:script_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_script(script_id):
    script = Script.query.get_or_404(script_id)
    
    # Get all submissions for this script
    submissions = Submission.query.filter_by(script_id=script_id).all()
    
    # Delete audio files and submissions
    deleted_files = 0
    for submission in submissions:
        if submission.audio_filename:
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], submission.audio_filename)
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    deleted_files += 1
                except Exception as e:
                    app.logger.error(f"Failed to delete audio file {audio_path}: {e}")
        
        # Delete the submission record
        db.session.delete(submission)
    
    # Delete the script
    db.session.delete(script)
    db.session.commit()
    
    app.logger.info(f"Deleted script {script_id} with {len(submissions)} submissions and {deleted_files} audio files")
    return jsonify({
        'success': True,
        'deleted_submissions': len(submissions),
        'deleted_files': deleted_files
    })

@app.route('/api/scripts/bulk-delete', methods=['DELETE'])
@require_role(['admin'])
def bulk_delete_scripts():
    data = request.json or {}
    script_ids = data.get('script_ids', [])
    
    if not script_ids:
        return jsonify({'success': False, 'error': 'No script IDs provided'}), 400
    
    # Validate that all IDs are integers
    try:
        script_ids = [int(id) for id in script_ids]
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid script ID format'}), 400
    
    # Delete scripts and their associated submissions
    total_deleted_scripts = 0
    total_deleted_submissions = 0
    total_deleted_files = 0
    
    for script_id in script_ids:
        script = Script.query.get(script_id)
        if not script:
            continue
        
        # Get all submissions for this script
        submissions = Submission.query.filter_by(script_id=script_id).all()
        
        # Delete audio files and submissions
        for submission in submissions:
            if submission.audio_filename:
                audio_path = os.path.join(app.config['UPLOAD_FOLDER'], submission.audio_filename)
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        total_deleted_files += 1
                    except Exception as e:
                        app.logger.error(f"Failed to delete audio file {audio_path}: {e}")
            
            db.session.delete(submission)
            total_deleted_submissions += 1
        
        # Delete the script
        db.session.delete(script)
        total_deleted_scripts += 1
    
    db.session.commit()
    
    app.logger.info(f"Bulk deleted {total_deleted_scripts} scripts with {total_deleted_submissions} submissions and {total_deleted_files} audio files")
    return jsonify({
        'success': True,
        'deleted_count': total_deleted_scripts,
        'deleted_submissions': total_deleted_submissions,
        'deleted_files': total_deleted_files
    })

@app.route('/api/scripts/bulk-upload', methods=['POST'])
@require_role(['admin'])
def bulk_upload_scripts():
    try:
        # Check if file was uploaded
        if 'csvFile' not in request.files:
            return jsonify({'success': False, 'error': 'No CSV file provided'}), 400
        
        csv_file = request.files['csvFile']
        language = request.form.get('language')
        
        if csv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not language:
            return jsonify({'success': False, 'error': 'Language selection is required'}), 400
        
        # Verify language exists
        if not Language.query.filter_by(code=language).first():
            return jsonify({'success': False, 'error': 'Invalid language selected'}), 400
        
        # Read and parse CSV content
        import csv
        import io
        
        # Read file content
        content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # Validate CSV has required column
        fieldnames = csv_reader.fieldnames or []
        if 'content' not in fieldnames:
            return jsonify({
                'success': False, 
                'error': 'CSV must have a "content" column. Found columns: ' + ', '.join(fieldnames)
            }), 400
        
        # Process CSV rows and create scripts
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 because header is row 1
            script_content = row.get('content', '').strip()
            
            if not script_content:
                errors.append(f"Row {row_num}: Empty content")
                continue
            
            # Check if script with same content and language already exists
            existing_script = Script.query.filter_by(content=script_content, language=language).first()
            if existing_script:
                errors.append(f"Row {row_num}: Script with same content already exists")
                continue
            
            try:
                # Create new script
                script = Script(
                    content=script_content,
                    language=language,
                    is_active=True
                )
                db.session.add(script)
                created_count += 1
            except Exception as e:
                errors.append(f"Row {row_num}: Error creating script - {str(e)}")
                continue
        
        # Commit all changes if at least one script was created
        if created_count > 0:
            db.session.commit()
        
        # Prepare response
        response_data = {'success': True, 'created_count': created_count}
        
        if errors:
            response_data['warnings'] = errors
            response_data['message'] = f"Created {created_count} scripts with {len(errors)} warnings"
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to process CSV: {str(e)}'}), 500

@app.route('/api/scripts/bulk-text', methods=['POST'])
@require_role(['admin'])
def bulk_add_text_scripts():
    """Bulk add scripts from multiline text where each line is a script"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        language = data.get('language')
        script_text = data.get('scriptText', '')
        
        if not language:
            return jsonify({'success': False, 'error': 'Language is required'}), 400
        
        if not script_text.strip():
            return jsonify({'success': False, 'error': 'Script text is required'}), 400
        
        # Verify language exists
        if not Language.query.filter_by(code=language).first():
            return jsonify({'success': False, 'error': 'Invalid language selected'}), 400
        
        # Split text into lines and process each one
        lines = [line.strip() for line in script_text.split('\n') if line.strip()]
        
        if not lines:
            return jsonify({'success': False, 'error': 'No valid script lines found'}), 400
        
        created_count = 0
        errors = []
        
        for line_num, content in enumerate(lines, start=1):
            # Check for duplicate
            existing_script = Script.query.filter_by(content=content, language=language).first()
            if existing_script:
                errors.append(f"Line {line_num}: Script with same content already exists")
                continue
            
            # Create script
            try:
                script = Script(
                    content=content,
                    language=language,
                    is_active=True
                )
                db.session.add(script)
                created_count += 1
            except Exception as e:
                errors.append(f"Line {line_num}: Error creating script - {str(e)}")
                continue
        
        # Commit all changes if at least one script was created
        if created_count > 0:
            db.session.commit()
        
        response_data = {'success': True, 'created_count': created_count}
        
        if errors:
            response_data['warnings'] = errors
            response_data['message'] = f"Created {created_count} scripts with {len(errors)} warnings"
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to process text: {str(e)}'}), 500

# Demographic requirement management APIs
@app.route('/api/scripts/<int:script_id>/requirements', methods=['GET'])
@require_role(['admin'])
def get_script_requirements(script_id):
    """Get demographic requirements for a script"""
    script = Script.query.get_or_404(script_id)
    requirements = ScriptVariantRequirement.query.filter_by(script_id=script_id).all()
    
    return jsonify({
        'script_id': script_id,
        'requirements': [{
            'id': req.id,
            'gender': req.gender,
            'age_group': req.age_group,
            'target_total': req.target_total,
            'enabled': req.enabled
        } for req in requirements]
    })

@app.route('/api/scripts/<int:script_id>/requirements', methods=['POST'])
@require_role(['admin'])
def set_script_requirements(script_id):
    """Set demographic requirements for a script"""
    script = Script.query.get_or_404(script_id)
    data = request.get_json()
    
    requirements = data.get('requirements', [])
    
    try:
        # Clear existing requirements
        ScriptVariantRequirement.query.filter_by(script_id=script_id).delete()
        
        # Add new requirements
        for req in requirements:
            variant_req = ScriptVariantRequirement(
                script_id=script_id,
                gender=req['gender'],
                age_group=req['age_group'],
                target_total=req.get('target_total', 1),
                enabled=req.get('enabled', True)
            )
            db.session.add(variant_req)
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scripts/<int:script_id>/progress', methods=['GET'])
@require_role(['admin', 'reviewer'])
def get_script_progress(script_id):
    """Get progress matrix for a script showing completed vs target by demographic"""
    script = Script.query.get_or_404(script_id)
    
    # Get requirements
    requirements = ScriptVariantRequirement.query.filter_by(script_id=script_id, enabled=True).all()
    
    # Get completion counts by demographic
    from sqlalchemy import func
    completion_counts = db.session.query(
        Submission.provider_gender,
        Submission.provider_age_group,
        Submission.status,
        func.count(Submission.id).label('count')
    ).filter_by(script_id=script_id).group_by(
        Submission.provider_gender, 
        Submission.provider_age_group,
        Submission.status
    ).all()
    
    # Build progress matrix
    progress = {}
    for req in requirements:
        key = f"{req.gender}_{req.age_group}"
        progress[key] = {
            'gender': req.gender,
            'age_group': req.age_group,
            'target': req.target_total,
            'approved': 0,
            'pending': 0,
            'rejected': 0
        }
    
    # Fill in actual counts
    for count_row in completion_counts:
        if count_row.provider_gender and count_row.provider_age_group:
            key = f"{count_row.provider_gender}_{count_row.provider_age_group}"
            if key in progress:
                if count_row.status == 'approved':
                    progress[key]['approved'] = count_row.count
                elif count_row.status == 'pending':
                    progress[key]['pending'] = count_row.count
                elif count_row.status == 'rejected':
                    progress[key]['rejected'] = count_row.count
    
    return jsonify({
        'script_id': script_id,
        'progress': list(progress.values())
    })

# Provider recording queue APIs
@app.route('/api/recording/next', methods=['GET'])
@require_auth
def get_next_recording_task():
    """Get the next script that needs recording for the current user's demographic"""
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    language = request.args.get('language', 'en')
    
    if not user.gender or not user.age_group:
        return jsonify({'error': 'User profile incomplete - gender and age group required'}), 400
    
    # Find scripts that need recordings for this user's demographic
    # and haven't been recorded by this user yet
    subquery = db.session.query(Submission.script_id).filter_by(user_id=user.id)
    
    available_scripts = db.session.query(Script, ScriptVariantRequirement).join(
        ScriptVariantRequirement, Script.id == ScriptVariantRequirement.script_id
    ).filter(
        Script.is_active == True,
        Script.language == language,
        ScriptVariantRequirement.enabled == True,
        ScriptVariantRequirement.gender == user.gender,
        ScriptVariantRequirement.age_group == user.age_group,
        ~Script.id.in_(subquery)  # User hasn't recorded this script yet
    ).order_by(Script.created_at.asc()).first()
    
    if not available_scripts:
        return jsonify({'message': 'No scripts available for your demographic profile', 'has_task': False})
    
    script, requirement = available_scripts
    
    # Check if we still need more recordings for this variant
    current_count = Submission.query.filter_by(
        script_id=script.id,
        provider_gender=user.gender,
        provider_age_group=user.age_group,
        status='approved'
    ).count()
    
    if current_count >= requirement.target_total:
        return jsonify({'message': 'Target reached for your demographic', 'has_task': False})
    
    return jsonify({
        'has_task': True,
        'script': {
            'id': script.id,
            'content': script.content,
            'language': script.language
        },
        'requirement': {
            'target_total': requirement.target_total,
            'current_approved': current_count
        },
        'user_demographic': {
            'gender': user.gender,
            'age_group': user.age_group
        }
    })

@app.route('/api/user-submissions/<int:script_id>', methods=['GET'])
@require_auth
def get_user_submissions(script_id):
    """Get submissions for a specific script - all submissions for admins, user's own for others"""
    user_id = session['user_id']
    user_role = session.get('user_role', 'provider')
    script = Script.query.get_or_404(script_id)
    
    # Admins see ALL submissions for this script
    if user_role == 'admin':
        submissions = Submission.query.filter_by(
            script_id=script_id
        ).order_by(Submission.created_at.desc()).all()
    else:
        # Non-admins only see their own submissions
        submissions = Submission.query.filter_by(
            user_id=user_id,
            script_id=script_id
        ).order_by(Submission.created_at.desc()).all()
    
    # Prepare submission data with submitter info for admins
    submission_data = []
    for sub in submissions:
        item = {
            'id': sub.id,
            'text_content': sub.text_content or '',
            'transcript': sub.transcript or '',
            'audio_filename': sub.audio_filename,
            'audio_url': f'/api/submissions/{sub.id}/audio' if sub.audio_filename else None,
            'status': sub.status,
            'created_at': sub.created_at.isoformat(),
            'word_count': sub.word_count or 0,
            'duration': sub.duration
        }
        
        # Add submitter info for admins
        if user_role == 'admin':
            if sub.is_field_collection:
                item['submitter'] = f"Field: {sub.speaker_name or 'Anonymous'}"
                item['submitter_type'] = 'field'
                item['speaker_location'] = sub.speaker_location or 'Unknown'
            else:
                user = User.query.get(sub.user_id) if sub.user_id else None
                item['submitter'] = f"{user.first_name} {user.last_name}" if user else 'Unknown'
                item['submitter_type'] = 'user'
        
        submission_data.append(item)
    
    return jsonify({
        'success': True,
        'script_id': script_id,
        'submissions': submission_data
    })

@app.route('/api/submissions/<int:submission_id>/audio', methods=['GET'])
@require_auth
def stream_submission_audio(submission_id):
    """Securely stream audio file for a submission"""
    user_id = session['user_id']
    user_role = session.get('user_role', 'provider')
    
    submission = Submission.query.get_or_404(submission_id)
    
    # Check authorization: admin can access all, others only their own
    if user_role != 'admin' and submission.user_id != user_id:
        abort(403)
    
    if not submission.audio_filename:
        abort(404)
    
    # Secure path handling with subdirectory support
    # Normalize path and ensure it stays within UPLOAD_FOLDER
    audio_filename = submission.audio_filename
    
    # Try different path combinations (for backwards compatibility)
    possible_paths = [
        os.path.join(app.config['UPLOAD_FOLDER'], audio_filename),
        os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio_filename),
        os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(audio_filename))
    ]
    
    audio_path = None
    for path in possible_paths:
        # Normalize and check it's within UPLOAD_FOLDER
        normalized_path = os.path.normpath(path)
        if normalized_path.startswith(os.path.normpath(app.config['UPLOAD_FOLDER'])) and os.path.exists(normalized_path):
            audio_path = normalized_path
            break
    
    if not audio_path:
        abort(404)
    
    # Determine mimetype
    mimetype = 'audio/webm'
    if audio_filename.endswith('.wav'):
        mimetype = 'audio/wav'
    elif audio_filename.endswith('.mp3'):
        mimetype = 'audio/mpeg'
    elif audio_filename.endswith('.mp4'):
        mimetype = 'audio/mp4'
    
    return send_file(audio_path, mimetype=mimetype)

# User management routes
@app.route('/admin/users')
@require_role(['admin'])
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/data-export')
@require_role(['admin'])
def admin_data_export():
    """View all recordings with metadata for export"""
    # Get language filter from query params
    language_filter = request.args.get('language', type=int)
    
    # Build query with optional language filter
    query = Submission.query
    if language_filter:
        query = query.filter_by(language_id=language_filter)
    
    submissions = query.order_by(Submission.created_at.desc()).all()
    
    # Enrich submissions with related data
    export_data = []
    for sub in submissions:
        script = Script.query.get(sub.script_id) if sub.script_id else None
        
        # Get submitter info
        if sub.is_field_collection:
            admin = User.query.get(sub.collected_by_admin_id) if sub.collected_by_admin_id else None
            submitter = f"{admin.first_name} {admin.last_name}" if admin else 'Unknown Admin'
            speaker_name = sub.speaker_name or 'Anonymous'
        else:
            user = User.query.get(sub.user_id) if sub.user_id else None
            submitter = f"{user.first_name} {user.last_name}" if user else 'Unknown User'
            speaker_name = submitter
        
        export_data.append({
            'submission': sub,
            'script_content': script.content if script else 'N/A',
            'script_language': script.language if script else 'N/A',
            'submitter': submitter,
            'speaker_name': speaker_name
        })
    
    # Get all active languages for the filter dropdown
    languages = Language.query.filter_by(is_active=True).order_by(Language.name).all()
    
    return render_template(
        'admin_data_export.html', 
        export_data=export_data, 
        total_count=len(export_data),
        languages=languages,
        selected_language=str(language_filter) if language_filter else ''
    )

@app.route('/admin/data-export/csv')
@require_role(['admin'])
def export_data_csv():
    """Export all recordings metadata as CSV"""
    # Get language filter from query params
    language_filter = request.args.get('language', type=int)
    
    # Build query with optional language filter
    query = Submission.query
    if language_filter:
        query = query.filter_by(language_id=language_filter)
    
    submissions = query.order_by(Submission.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Audio Filename', 'Script ID', 'Script Content', 'Transcript', 'Language',
        'Speaker Gender', 'Speaker Age Group', 'Speaker Name', 'Speaker Location',
        'Is Field Collection', 'Collected By', 'Status', 'Word Count', 'Created At'
    ])
    
    # Write data rows
    for sub in submissions:
        script = Script.query.get(sub.script_id) if sub.script_id else None
        
        # Get collector info
        if sub.is_field_collection:
            admin = User.query.get(sub.collected_by_admin_id) if sub.collected_by_admin_id else None
            collector = f"{admin.first_name} {admin.last_name}" if admin else 'Unknown'
        else:
            user = User.query.get(sub.user_id) if sub.user_id else None
            collector = f"{user.first_name} {user.last_name}" if user else 'Unknown'
        
        writer.writerow([
            sub.id,
            sub.audio_filename or '',
            sub.script_id or '',
            script.content if script else '',
            sub.transcript or '',
            script.language if script else '',
            sub.provider_gender or '',
            sub.provider_age_group or '',
            sub.speaker_name or '',
            sub.speaker_location or '',
            'Yes' if sub.is_field_collection else 'No',
            collector,
            sub.status,
            sub.word_count or 0,
            sub.created_at.strftime('%Y-%m-%d %H:%M:%S') if sub.created_at else ''
        ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'voicescript_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
@require_role(['admin'])
def admin_delete_submission(submission_id):
    """Admin: Delete any submission and its audio file"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Delete audio file if exists (with same path resolution as stream endpoint)
    deleted_file = False
    if submission.audio_filename:
        audio_filename = submission.audio_filename
        
        # Try different path combinations (same as stream endpoint)
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], audio_filename),
            os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio_filename),
            os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(audio_filename))
        ]
        
        audio_path = None
        for path in possible_paths:
            # Normalize and check it's within UPLOAD_FOLDER
            normalized_path = os.path.normpath(path)
            if normalized_path.startswith(os.path.normpath(app.config['UPLOAD_FOLDER'])) and os.path.exists(normalized_path):
                audio_path = normalized_path
                break
        
        if audio_path:
            try:
                os.remove(audio_path)
                deleted_file = True
                app.logger.info(f"Deleted audio file: {audio_path}")
            except Exception as e:
                app.logger.error(f"Failed to delete audio file {audio_path}: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to delete audio file: {str(e)}'
                }), 500
        else:
            app.logger.warning(f"Audio file not found for submission {submission_id}: {audio_filename}")
    
    # Delete the submission record
    db.session.delete(submission)
    db.session.commit()
    
    app.logger.info(f"Deleted submission {submission_id} (audio file deleted: {deleted_file})")
    return jsonify({
        'success': True,
        'deleted_file': deleted_file
    })

@app.route('/admin/roles')
@require_role(['admin'])
def admin_roles():
    users = User.query.order_by(User.created_at.desc()).all()
    role_stats = {
        'admin': User.query.filter_by(role='admin').count(),
        'reviewer': User.query.filter_by(role='reviewer').count(),
        'provider': User.query.filter_by(role='provider').count()
    }
    return render_template('admin_roles.html', users=users, role_stats=role_stats)

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
@require_role(['admin'])
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json or {}
    
    new_role = data.get('role')
    if new_role not in ['provider', 'reviewer', 'admin']:
        return jsonify({'success': False, 'error': 'Invalid role'}), 400
    
    user.role = new_role
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users', methods=['POST'])
@require_role(['admin'])
def create_user():
    data = request.json or {}
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'error': 'User already exists'}), 400
    
    user = User(
        email=data['email'],
        first_name=data['first_name'], 
        last_name=data['last_name'],
        role=data.get('role', 'provider'),
        gender=data.get('gender'),
        age_group=data.get('age_group')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'id': user.id})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_role(['admin'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json or {}
    
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.gender = data.get('gender', user.gender)
    user.age_group = data.get('age_group', user.age_group)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the current user
    if user.id == session.get('user_id'):
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

# Language management API routes
@app.route('/api/languages', methods=['POST'])
@require_role(['admin'])
def add_language():
    data = request.json or {}
    
    # Check if language code already exists
    if Language.query.filter_by(code=data['code']).first():
        return jsonify({'success': False, 'error': 'Language code already exists'}), 400
    
    language = Language(
        code=data['code'].lower(),
        name=data['name'],
        native_name=data.get('native_name', ''),
        is_active=True
    )
    db.session.add(language)
    
    # Create pricing rates if provided
    provider_rate = float(data.get('provider_rate', 0.010))
    reviewer_rate = float(data.get('reviewer_rate', 2.00))
    
    pricing = PricingRate(
        language_code=data['code'].lower(),
        provider_rate_per_word=provider_rate,
        reviewer_rate_per_submission=reviewer_rate,
        currency=data.get('currency', 'USD')
    )
    db.session.add(pricing)
    
    db.session.commit()
    return jsonify({'success': True, 'id': language.id})



@app.route('/api/languages/<language_code>', methods=['PUT'])
@require_role(['admin'])
def update_language(language_code):
    language = Language.query.filter_by(code=language_code).first()
    if not language:
        return jsonify({'success': False, 'error': 'Language not found'}), 404
    
    data = request.json or {}
    language.name = data.get('name', language.name)
    language.native_name = data.get('native_name', language.native_name)
    language.is_active = data.get('is_active', language.is_active)
    
    # Update or create pricing if rates provided
    if 'provider_rate' in data or 'reviewer_rate' in data:
        pricing = PricingRate.query.filter_by(language_code=language_code).first()
        if pricing:
            pricing.provider_rate_per_word = float(data.get('provider_rate', pricing.provider_rate_per_word))
            pricing.reviewer_rate_per_submission = float(data.get('reviewer_rate', pricing.reviewer_rate_per_submission))
            pricing.currency = data.get('currency', pricing.currency)
            pricing.updated_at = datetime.utcnow()
        else:
            pricing = PricingRate(
                language_code=language_code,
                provider_rate_per_word=float(data.get('provider_rate', 0.01)),
                reviewer_rate_per_submission=float(data.get('reviewer_rate', 2.00)),
                currency=data.get('currency', 'USD')
            )
            db.session.add(pricing)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/languages/<language_code>', methods=['GET'])
@require_role(['admin'])
def get_language(language_code):
    """Get language details"""
    language = Language.query.filter_by(code=language_code).first()
    if not language:
        return jsonify({'success': False, 'error': 'Language not found'}), 404
    
    return jsonify({
        'code': language.code,
        'name': language.name,
        'native_name': language.native_name,
        'is_active': language.is_active
    })

@app.route('/api/pricing/<language_code>', methods=['GET'])
@require_role(['admin'])
def get_pricing(language_code):
    """Get pricing for a language"""
    pricing = PricingRate.query.filter_by(language_code=language_code).first()
    if not pricing:
        return jsonify({
            'provider_rate_per_word': 0.010,
            'reviewer_rate_per_submission': 2.00,
            'currency': 'USD'
        })
    
    return jsonify({
        'provider_rate_per_word': pricing.provider_rate_per_word,
        'reviewer_rate_per_submission': pricing.reviewer_rate_per_submission,
        'currency': pricing.currency
    })

@app.route('/api/settings/earnings', methods=['PUT'])
@require_role(['admin'])
def update_earnings_setting():
    """Update earnings visibility setting"""
    # Validate request has JSON content
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    show_earnings = data.get('show_earnings')
    
    # Strict validation of input values
    if show_earnings is None:
        return jsonify({'success': False, 'error': 'show_earnings field is required'}), 400
    
    if not isinstance(show_earnings, str) or show_earnings not in ['true', 'false']:
        return jsonify({'success': False, 'error': 'Invalid value. Must be "true" or "false"'}), 400
    
    try:
        set_app_setting('show_earnings', show_earnings, 'Whether to display earnings functionality throughout the application')
        return jsonify({
            'success': True, 
            'message': 'Settings updated successfully',
            'show_earnings': show_earnings
        })
    except Exception as e:
        app.logger.error(f"Error updating earnings setting: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

def create_demo_data(force=False):
    """Create demo users and initial data - Development only"""
    if is_production and not force:
        app.logger.warning("Attempted to create demo data in production - skipping")
        return
        
    try:
        # Create demo users if they don't exist - matching init_data.sql exactly
        demo_users = [
            {'email': 'admin@demo.com', 'password': 'demo123', 'first_name': 'Demo', 'last_name': 'Admin', 'role': 'admin', 'gender': 'prefer-not-to-say', 'age_group': 'Adult (20–59)'},
            {'email': 'provider@demo.com', 'password': 'demo123', 'first_name': 'Demo', 'last_name': 'Provider', 'role': 'provider', 'gender': 'female', 'age_group': 'Adult (20–59)'},
            {'email': 'reviewer@demo.com', 'password': 'demo123', 'first_name': 'Demo', 'last_name': 'Reviewer', 'role': 'reviewer', 'gender': 'male', 'age_group': 'Adult (20–59)'},
            {'email': 'john.provider@example.com', 'password': 'demo123', 'first_name': 'John', 'last_name': 'Smith', 'role': 'provider', 'gender': 'male', 'age_group': 'Teen (13–19)'},
            {'email': 'maria.provider@example.com', 'password': 'demo123', 'first_name': 'Maria', 'last_name': 'Rodriguez', 'role': 'provider', 'gender': 'female', 'age_group': 'Elderly (60+)'},
            {'email': 'male.child@demo.com', 'password': 'demo123', 'first_name': 'Alex', 'last_name': 'Johnson', 'role': 'provider', 'gender': 'male', 'age_group': 'Child (0–12)'},
            {'email': 'male.teen@demo.com', 'password': 'demo123', 'first_name': 'Ryan', 'last_name': 'Davis', 'role': 'provider', 'gender': 'male', 'age_group': 'Teen (13–19)'},
            {'email': 'male.adult@demo.com', 'password': 'demo123', 'first_name': 'Michael', 'last_name': 'Brown', 'role': 'provider', 'gender': 'male', 'age_group': 'Adult (20–59)'},
            {'email': 'male.elderly@demo.com', 'password': 'demo123', 'first_name': 'Robert', 'last_name': 'Wilson', 'role': 'provider', 'gender': 'male', 'age_group': 'Elderly (60+)'},
            {'email': 'female.child@demo.com', 'password': 'demo123', 'first_name': 'Emma', 'last_name': 'Taylor', 'role': 'provider', 'gender': 'female', 'age_group': 'Child (0–12)'},
            {'email': 'female.teen@demo.com', 'password': 'demo123', 'first_name': 'Sophie', 'last_name': 'Anderson', 'role': 'provider', 'gender': 'female', 'age_group': 'Teen (13–19)'},
            {'email': 'female.adult@demo.com', 'password': 'demo123', 'first_name': 'Jessica', 'last_name': 'Martinez', 'role': 'provider', 'gender': 'female', 'age_group': 'Adult (20–59)'},
            {'email': 'female.elderly@demo.com', 'password': 'demo123', 'first_name': 'Margaret', 'last_name': 'Garcia', 'role': 'provider', 'gender': 'female', 'age_group': 'Elderly (60+)'}
        ]
        
        for user_data in demo_users:
            # Check if user exists by trying to query, but handle schema errors gracefully
            try:
                existing_user = User.query.filter_by(email=user_data['email']).first()
            except Exception:
                existing_user = None
                
            if not existing_user:
                user = User(
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    gender=user_data.get('gender', 'prefer-not-to-say'),
                    age_group=user_data.get('age_group', 'Adult (20–59)'),
                    auth_provider='local'  # Set default auth provider for demo users
                )
                user.set_password(user_data['password'])
                db.session.add(user)
        
        # Create demo scripts - matching init_data.sql exactly
        demo_scripts = [
            {'content': 'Hello, my name is [Your Name] and I am from [Your Location]. I am excited to contribute to this voice data collection project.', 'language': 'en', 'is_active': True},
            {'content': 'Today is a beautiful sunny day with clear blue skies. The temperature is perfect for outdoor activities.', 'language': 'en', 'is_active': True},
            {'content': 'Once upon a time, in a land far away, there lived a wise old owl who helped all the forest animals solve their problems.', 'language': 'en', 'is_active': True},
            {'content': 'Please read the following numbers clearly: 123, 456, 789, 1000, 2023, 15.5, 99.99, 0.01', 'language': 'en', 'is_active': True},
            {'content': 'Artificial intelligence, machine learning, natural language processing, neural networks, deep learning, algorithm', 'language': 'en', 'is_active': True}
        ]
        
        for script_data in demo_scripts:
            try:
                existing_script = Script.query.filter_by(content=script_data['content']).first()
            except Exception:
                existing_script = None
                
            if not existing_script:
                script = Script(**script_data)
                db.session.add(script)
        
        # Create demo languages with pricing - matching init_data.sql exactly
        demo_languages = [
            {'name': 'English', 'code': 'en', 'native_name': 'English', 'provider_rate': 0.01, 'reviewer_rate': 2.00, 'currency': 'USD'},
            {'name': 'Spanish', 'code': 'es', 'native_name': 'Español', 'provider_rate': 0.012, 'reviewer_rate': 2.20, 'currency': 'USD'},
            {'name': 'French', 'code': 'fr', 'native_name': 'Français', 'provider_rate': 0.013, 'reviewer_rate': 2.30, 'currency': 'USD'},
            {'name': 'German', 'code': 'de', 'native_name': 'Deutsch', 'provider_rate': 0.014, 'reviewer_rate': 2.40, 'currency': 'USD'},
            {'name': 'Bengali', 'code': 'bn', 'native_name': 'বাংলা', 'provider_rate': 0.015, 'reviewer_rate': 2.50, 'currency': 'USD'},
            {'name': 'Hindi', 'code': 'hi', 'native_name': 'हिन्दी', 'provider_rate': 0.015, 'reviewer_rate': 2.50, 'currency': 'USD'},
            {'name': 'Arabic', 'code': 'ar', 'native_name': 'العربية', 'provider_rate': 0.016, 'reviewer_rate': 2.60, 'currency': 'USD'},
            {'name': 'Chinese', 'code': 'zh', 'native_name': '中文', 'provider_rate': 0.018, 'reviewer_rate': 2.80, 'currency': 'USD'},
            {'name': 'Japanese', 'code': 'ja', 'native_name': '日本語', 'provider_rate': 0.020, 'reviewer_rate': 3.00, 'currency': 'USD'},
            {'name': 'Korean', 'code': 'ko', 'native_name': '한국어', 'provider_rate': 0.020, 'reviewer_rate': 3.00, 'currency': 'USD'},
        ]
        
        for lang_data in demo_languages:
            try:
                existing_language = Language.query.filter_by(code=lang_data['code']).first()
            except Exception:
                existing_language = None
                
            if not existing_language:
                # Create language
                language = Language(
                    name=lang_data['name'],
                    code=lang_data['code'],
                    native_name=lang_data['native_name'],
                    is_active=True
                )
                db.session.add(language)
                
                # Create corresponding pricing
                pricing = PricingRate(
                    language_code=lang_data['code'],
                    provider_rate_per_word=lang_data['provider_rate'],
                    reviewer_rate_per_submission=lang_data['reviewer_rate'],
                    currency=lang_data['currency']
                )
                db.session.add(pricing)
        
        db.session.commit()
        app.logger.info("Database initialized with demo data")
        
    except Exception as e:
        app.logger.error(f"Error creating demo data: {e}")
        db.session.rollback()



# Initialize database when the module is loaded (for both dev and production)
def init_database():
    """
    Initialize database with schema and demo data.
    Supports both migration-based (preferred) and SQLAlchemy-based (fallback) workflows.
    """
    with app.app_context():
        try:
            # Try migration-based approach first (check if schema_version table exists)
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(db.text("SELECT 1 FROM schema_version LIMIT 1"))
                    result.fetchone()
                app.logger.info("Database initialized via migrations")
            except:
                # Fallback: Use SQLAlchemy db.create_all() if migrations haven't run
                app.logger.info("Migration table not found, using SQLAlchemy to create schema...")
                db.create_all()
                app.logger.info("Database tables created via SQLAlchemy")
            
            # Only create demo data in development mode
            if os.environ.get('FLASK_ENV') != 'production':
                if User.query.count() == 0:
                    create_demo_data()
                    app.logger.info("Database initialized with demo data")
                else:
                    app.logger.info("Database already contains data, skipping demo data creation")
            else:
                app.logger.info("Production mode: Demo data creation skipped")
                
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
            if os.environ.get('FLASK_ENV') == 'production':
                raise  # Fail fast in production


# Health check endpoint for Docker
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker container monitoring"""
    try:
        # Test database connection
        result = db.session.execute(db.text('SELECT 1'))
        result.fetchone()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

# Production error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# Security headers for production
@app.after_request
def after_request(response):
    if is_production:
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Flask CLI Commands
@app.cli.command('seed-demo')
@click.option('--force', is_flag=True, help='Force recreation of demo data (clears existing demo data first)')
@click.option('--yes', is_flag=True, help='Skip confirmation prompt in production')
def seed_demo_command(force, yes):
    """Seed database with demo data for development and testing."""
    
    # Production safety check
    if is_production:
        if not yes:
            app.logger.error("❌ Cannot seed demo data in production without --yes flag")
            app.logger.error("   Use: flask seed-demo --force --yes (if you really know what you're doing)")
            return
        app.logger.warning("⚠️  Seeding demo data in PRODUCTION mode (--yes flag provided)")
    
    with app.app_context():
        try:
            # If force flag is set, delete existing demo data first
            if force:
                app.logger.info("🗑️  Force flag set - removing existing demo data...")
                
                # Delete demo users (by known email patterns)
                demo_emails = [
                    'provider@demo.com', 'reviewer@demo.com', 'admin@demo.com',
                    'john.provider@example.com', 'maria.provider@example.com',
                    'male.child@demo.com', 'male.teen@demo.com', 'male.adult@demo.com', 'male.elderly@demo.com',
                    'female.child@demo.com', 'female.teen@demo.com', 'female.adult@demo.com', 'female.elderly@demo.com'
                ]
                deleted_users = User.query.filter(User.email.in_(demo_emails)).delete(synchronize_session=False)
                
                # Delete demo scripts (by known titles)
                demo_titles = ['Introduction Script', 'Weather Description', 'Story Reading']
                deleted_scripts = Script.query.filter(Script.title.in_(demo_titles)).delete(synchronize_session=False)
                
                db.session.commit()
                app.logger.info(f"   ✅ Deleted {deleted_users} demo users, {deleted_scripts} demo scripts")
            
            # Count existing data before seeding
            users_before = User.query.count()
            scripts_before = Script.query.count()
            languages_before = Language.query.count()
            
            # Create demo data
            app.logger.info("🌱 Seeding demo data...")
            create_demo_data(force=True)  # Always run when using CLI command
            
            # Count after seeding
            users_after = User.query.count()
            scripts_after = Script.query.count()
            languages_after = Language.query.count()
            
            # Summary
            app.logger.info("✅ Demo data seeding completed successfully!")
            app.logger.info(f"   📊 Users: {users_before} → {users_after} (+{users_after - users_before})")
            app.logger.info(f"   📄 Scripts: {scripts_before} → {scripts_after} (+{scripts_after - scripts_before})")
            app.logger.info(f"   🌍 Languages: {languages_before} → {languages_after} (+{languages_after - languages_before})")
            app.logger.info("")
            app.logger.info("🔑 Demo Accounts (all use password: demo123):")
            app.logger.info("   👤 provider@demo.com (Provider role)")
            app.logger.info("   👤 reviewer@demo.com (Reviewer role)")
            app.logger.info("   👤 admin@demo.com (Admin role)")
            
        except Exception as e:
            app.logger.error(f"❌ Error seeding demo data: {e}")
            db.session.rollback()
            raise

@app.cli.command('migrate-field-collection')
def migrate_field_collection_command():
    """Add field collection columns to submissions table"""
    with app.app_context():
        try:
            app.logger.info("🔄 Adding field collection columns to submissions table...")
            
            # Add new columns to submissions table
            with db.engine.connect() as conn:
                # Make user_id nullable
                conn.execute(text("ALTER TABLE submissions ALTER COLUMN user_id DROP NOT NULL"))
                conn.commit()
                
                # Add new columns if they don't exist
                try:
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN collected_by_admin_id INTEGER REFERENCES users(id)"))
                    conn.commit()
                except Exception:
                    pass  # Column already exists
                
                try:
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN speaker_name VARCHAR(100)"))
                    conn.commit()
                except Exception:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN speaker_location VARCHAR(255)"))
                    conn.commit()
                except Exception:
                    pass
                
                try:
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN is_field_collection BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                except Exception:
                    pass
            
            app.logger.info("✅ Field collection migration completed successfully!")
            
        except Exception as e:
            app.logger.error(f"❌ Error during migration: {e}")
            raise

# Initialize database on module load
init_database()

if __name__ == '__main__':
    # Direct execution mode - use proper WSGI server for production
    port = int(os.environ.get('PORT', 8000))
    
    if is_production:
        app.logger.warning("⚠️  Running with built-in server in production mode")
        app.logger.warning("⚠️  Use Gunicorn or similar WSGI server for production deployment")
        app.logger.info(f"Starting VoiceScript Collector on port {port}")
    else:
        app.logger.info("🔧 Starting in development mode")
        app.logger.info(f"🚀 VoiceScript Collector: http://localhost:{port}")
        app.logger.info("👤 Demo Accounts: provider@demo.com, reviewer@demo.com, admin@demo.com (password: demo123)")
    
    app.run(host='0.0.0.0', port=port, debug=not is_production)