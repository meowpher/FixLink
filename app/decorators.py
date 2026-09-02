"""
Centralized Authentication Decorators for FixLink.
Provides wraps for Admin, Professional, User, and SuperAdmin access control.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request
from .api_utils import api_response

def login_required(f):
    """Decorator to require any valid login (User, Admin, or Professional)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'professional_id' not in session:
            # Handle AJAX or JSON requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Authentication required. Please log in.', status=401)
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            # Handle AJAX requests by returning 401 JSON instead of redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_response(success=False, error='Admin access required. Please log in again.', status=401)
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        
        from .models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            session.pop('user_id', None)
            session.pop('is_admin', None)
            session.pop('user_name', None)
            session.pop('user_role', None)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_response(success=False, error='Admin access required.', status=401)
            flash('Admin account not found or access revoked.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def user_login_required(f):
    """Decorator to require user login (reporter or admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Handle AJAX requests by returning 401 JSON instead of redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            from .blueprints.auth.routes import login as auth_login
            return auth_login()
        
        from .models import User
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            session.pop('is_admin', None)
            session.pop('user_name', None)
            session.pop('user_role', None)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            from .blueprints.auth.routes import login as auth_login
            return auth_login()
        return f(*args, **kwargs)
    return decorated_function

def faculty_login_required(f):
    """Decorator to require faculty login (or admin for testing)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .models import User
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            from .blueprints.auth.routes import login as auth_login
            return auth_login()
            
        role = session.get('user_role')
        is_admin = session.get('is_admin')
        if role != User.ROLE_FACULTY and not is_admin:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Faculty access required.', status=403)
            flash('Faculty access required.', 'error')
            return redirect(url_for('main.report_form'))
        return f(*args, **kwargs)
    return decorated_function

def professional_login_required(f):
    """Decorator to require professional login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'professional_id' not in session:
            # Handle AJAX requests by returning 401 JSON instead of redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            from .blueprints.auth.routes import login as auth_login
            return auth_login()
        
        from .models import Professional
        prof = Professional.query.get(session['professional_id'])
        if not prof:
            session.pop('professional_id', None)
            session.pop('professional_name', None)
            session.pop('professional_category', None)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_response(success=False, error='Account not found. Please log in again.', status=401)
            flash('Professional account not found or session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login', pro=1))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_super_admin'):
            # Handle AJAX requests by returning 401 JSON instead of redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_response(success=False, error='SuperAdmin access required.', status=401)
            return redirect(url_for('superadmin.login'))
        return f(*args, **kwargs)
    return decorated_function
