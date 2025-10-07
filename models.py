from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Made nullable for OAuth users
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='provider')
    gender = db.Column(db.String(20), nullable=True)  # male, female, non-binary, prefer-not-to-say
    age_group = db.Column(db.String(20), nullable=True)  # Child (0–12), Teen (13–19), Adult (20–59), Elderly (60+)
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # Google OAuth ID
    profile_picture = db.Column(db.String(255), nullable=True)  # Profile picture URL
    auth_provider = db.Column(db.String(20), default='local')  # 'local' or 'google'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Script(db.Model):
    __tablename__ = 'scripts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    target_duration = db.Column(db.Integer)  # in seconds
    language = db.Column(db.String(10), default='en')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScriptVariantRequirement(db.Model):
    __tablename__ = 'script_variant_requirements'
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)
    gender = db.Column(db.String(20), nullable=False)  # male, female, non-binary, prefer-not-to-say
    age_group = db.Column(db.String(20), nullable=False)  # Child (0-12), Teen (13-19), Adult (20-59), Elderly (60+)
    target_total = db.Column(db.Integer, default=1, nullable=False)  # How many recordings needed for this variant
    enabled = db.Column(db.Boolean, default=True, nullable=False)  # Whether this variant is actively being collected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    script = db.relationship('Script', backref='variant_requirements')
    
    # Ensure unique combination of script + gender + age_group
    __table_args__ = (db.UniqueConstraint('script_id', 'gender', 'age_group', name='unique_script_variant'),)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for field-collected submissions
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False)  # Required for script-based recordings
    text_content = db.Column(db.Text)  # Optional text response
    transcript = db.Column(db.Text)  # Real-time transcription from Web Speech API
    audio_filename = db.Column(db.String(255), nullable=False)  # Audio required for script recordings
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_notes = db.Column(db.Text)
    quality_score = db.Column(db.Integer)
    word_count = db.Column(db.Integer, default=0)
    duration = db.Column(db.Float, default=0.0)  # Changed from duration_seconds for consistency
    # Demographic snapshot columns for variant tracking
    provider_gender = db.Column(db.String(20), nullable=True)  # Snapshot of user's gender at submission time
    provider_age_group = db.Column(db.String(20), nullable=True)  # Snapshot of user's age_group at submission time
    
    # Field collection metadata (when admin collects on behalf of anonymous speaker)
    collected_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who collected this
    speaker_name = db.Column(db.String(100), nullable=True)  # Anonymous speaker's name (optional)
    speaker_location = db.Column(db.String(255), nullable=True)  # Where recording was collected
    is_field_collection = db.Column(db.Boolean, default=False)  # Flag to identify field-collected submissions
    
    user = db.relationship('User', foreign_keys=[user_id])
    script = db.relationship('Script')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    collected_by_admin = db.relationship('User', foreign_keys=[collected_by_admin_id])

class BillingRecord(db.Model):
    __tablename__ = 'billing_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    rate_per_word = db.Column(db.Float)  # For provider payments
    rate_per_submission = db.Column(db.Float)  # For reviewer payments
    billing_type = db.Column(db.String(20), nullable=False)  # 'provider' or 'reviewer'
    language_code = db.Column(db.String(10), nullable=False)
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    submission = db.relationship('Submission')

class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    native_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PricingRate(db.Model):
    __tablename__ = 'pricing_rates'
    id = db.Column(db.Integer, primary_key=True)
    language_code = db.Column(db.String(10), db.ForeignKey('languages.code'), nullable=False)
    provider_rate_per_word = db.Column(db.Float, default=0.01)  # Rate paid to providers
    reviewer_rate_per_submission = db.Column(db.Float, default=2.00)  # Fixed rate per review
    currency = db.Column(db.String(10), default='USD')  # Currency code (USD, EUR, BDT, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    language = db.relationship('Language')

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
