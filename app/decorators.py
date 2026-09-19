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
            # Handle AJAX or JSON API requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Admin access required. Please log in again.', status=403)
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        
        from .models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            session.pop('user_id', None)
            session.pop('is_admin', None)
            session.pop('user_name', None)
            session.pop('user_role', None)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Admin access required.', status=403)
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
            return redirect(url_for('auth.login'))
        
        from .models import User
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            session.pop('is_admin', None)
            session.pop('user_name', None)
            session.pop('user_role', None)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            return redirect(url_for('auth.login'))
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
            return redirect(url_for('auth.login'))
            
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
            return redirect(url_for('auth.login', pro=1))
        
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
        
        # Clean up any lingering professional session keys on developer's site
        if 'professional_id' in session:
            session.pop('professional_id', None)
            session.pop('professional_name', None)
            session.pop('professional_category', None)
            
        return f(*args, **kwargs)
    return decorated_function

def require_ownership(model_class, id_param='id', owner_field='user_id', allow_admin=True):
    """
    IDOR Prevention Decorator:
    Enforces that the current authenticated user owns the database record being accessed/modified.
    
    :param model_class: The SQLAlchemy Model class (e.g., RoomBooking, Ticket, Timetable, BugReport).
    :param id_param: The URL keyword argument name containing the record's Primary Key.
    :param owner_field: The attribute name on the model representing the owner (e.g., 'user_id', 'faculty_id', 'reporter_id').
    :param allow_admin: Whether administrators/superadmins can override ownership checks.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Verify user is authenticated
            current_user_id = session.get('user_id') or session.get('professional_id')
            if not current_user_id:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                    return api_response(success=False, error='Authentication required.', status=401)
                return redirect(url_for('auth.login'))

            # 2. Extract record ID from route parameters (or request payload)
            record_id = kwargs.get(id_param) or (request.view_args.get(id_param) if request.view_args else None)
            if not record_id:
                return api_response(success=False, error=f'Missing parameter {id_param}', status=400)

            # 3. Retrieve target record from database
            record = model_class.query.get(record_id)
            if not record:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                    return api_response(success=False, error='Resource not found.', status=404)
                flash('The requested resource was not found.', 'error')
                return redirect(url_for('main.index'))

            # 4. Check for Administrative / SuperAdmin Override
            is_admin = session.get('is_admin', False) or session.get('is_super_admin', False)
            if allow_admin and is_admin:
                return f(*args, **kwargs)

            # 5. Enforce strict IDOR ownership match
            record_owner_id = getattr(record, owner_field, None)
            
            # If owner doesn't match current session -> INSTANT 403 FORBIDDEN
            if record_owner_id is None or str(record_owner_id) != str(current_user_id):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                    return api_response(
                        success=False,
                        error='Access Denied: You do not have permission to modify this resource.',
                        status=403
                    )
                flash('Access Denied: You cannot modify a record that does not belong to you.', 'error')
                return redirect(url_for('main.index')), 403

            # Authorized -> Proceed to route handler
            return f(*args, **kwargs)
        return decorated_function
    return decorator
