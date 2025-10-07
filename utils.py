import os
import functools
from flask import session, redirect, url_for, flash, request
from models import AppSettings, db
from datetime import datetime

# App settings helpers
def get_app_setting(key, default_value=''):
    """Get application setting value with fallback to default"""
    setting = AppSettings.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else default_value

def get_show_earnings():
    """Get earnings visibility setting as boolean"""
    setting_value = get_app_setting('show_earnings', 'true')
    return setting_value.lower() == 'true'

def set_app_setting(key, value, description=''):
    """Set application setting value"""
    setting = AppSettings.query.filter_by(setting_key=key).first()
    if setting:
        setting.setting_value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSettings(
            setting_key=key,
            setting_value=value,
            description=description
        )
        db.session.add(setting)
    db.session.commit()

# Authentication decorators
def require_auth(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Get app and is_production from current app context
        from flask import current_app as app
        is_production = os.environ.get('FLASK_ENV') == 'production'
        
        # Primary session authentication
        if 'user_id' in session:
            return f(*args, **kwargs)
        
        # Fallback authentication ONLY in development mode (SECURITY: disabled in production)
        enable_fallback = os.environ.get('ENABLE_WEBVIEW_FALLBACK', 'false').lower() == 'true'
        
        if enable_fallback and not is_production:
            # Fallback authentication for Replit webview environment (DEV ONLY)
            fallback_cookies = [
                request.cookies.get('voicescript_session'),
                request.cookies.get('replit_auth_backup'),
                request.cookies.get('session_backup')
            ]
            
            for cookie_auth in fallback_cookies:
                if cookie_auth:
                    try:
                        user_id, user_role, user_name = cookie_auth.split(':', 2)
                        session.permanent = True
                        session['user_id'] = int(user_id)
                        session['user_role'] = user_role
                        session['user_name'] = user_name
                        session.modified = True
                        app.logger.warning(f"Fallback auth used: {user_role} (DEV ONLY)")
                        return f(*args, **kwargs)
                    except (ValueError, IndexError):
                        continue
            
            # Last resort: Check URL token for webview authentication (DEV ONLY)
            auth_token = request.args.get('auth_token')
            if auth_token:
                try:
                    user_id, user_role, user_name = auth_token.split(':', 2)
                    session.permanent = True
                    session['user_id'] = int(user_id)
                    session['user_role'] = user_role
                    session['user_name'] = user_name
                    session.modified = True
                    app.logger.warning(f"Token auth used: {user_role} (DEV ONLY)")
                    return f(*args, **kwargs)
                except (ValueError, IndexError):
                    pass
        
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    return decorated_function

def require_role(required_roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in required_roles:
                flash('Access denied. Insufficient privileges.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Context processor for template variables
def inject_common_variables():
    """Make common variables available to all templates"""
    show_earnings_setting = get_show_earnings()
    return dict(global_show_earnings=show_earnings_setting)
