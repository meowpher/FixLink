"""
Centralized Authentication Decorators for FixLink.
Provides wraps for Admin, Professional, User, and SuperAdmin access control.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, g
from .api_utils import api_response

def _get_authenticated_user():
    """Retrieve authenticated user using g cache or resilient database session query."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    if getattr(g, '_current_user_id', None) == user_id and getattr(g, '_current_user_cached', None) is not None:
        return g._current_user_cached
    from . import db
    from .models import User
    try:
        user = db.session.get(User, user_id)
    except Exception:
        try:
            db.session.rollback()
            db.session.remove()
            user = db.session.get(User, user_id)
        except Exception:
            user = None
    if user:
        g._current_user_cached = user
        g._current_user_id = user.id
    else:
        g._current_user_cached = None
        g._current_user_id = None
    return user

def login_required(f):
    """Decorator to require any valid user login (Student, Faculty, or Admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
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
        is_admin_session = session.get('is_admin') or session.get('is_super_admin')
        if ('user_id' not in session and not session.get('is_super_admin')) or not is_admin_session:
            # Handle AJAX or JSON API requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Admin access required. Please log in again.', status=403)
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        
        user = _get_authenticated_user()
        if not user and session.get('super_admin_email'):
            from .models import User
            try:
                user = User.query.filter_by(email=session['super_admin_email']).first()
            except Exception:
                user = None
            if user:
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin or True
        
        if not session.get('is_super_admin') and (not user or not (user.is_admin or user.is_supervisor or user.is_super_admin)):
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
        
        user = _get_authenticated_user()
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
    """Decorator to require faculty login (or admin for testing). Disallows students and peons."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .models import User
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Session expired. Please log in again.', status=401)
            return redirect(url_for('auth.login'))
            
        role = str(session.get('user_role') or '').upper()
        is_admin = session.get('is_admin') or session.get('is_super_admin')

        # Check designation (from session or database fallback)
        designation = str(session.get('user_designation') or '').strip().lower()
        if not designation:
            user = _get_authenticated_user()
            if user:
                designation = (user.designation or '').strip().lower()
                session['user_designation'] = user.designation

        is_peon = (designation == 'peon')

        # Strictly allow ONLY faculties (excluding peons) and administrators
        if (role != User.ROLE_FACULTY or is_peon) and not is_admin:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Faculty access required. Peons and students are not authorized.', status=403)
            flash('Faculty portal access is restricted to teaching and administrative faculty.', 'error')
            return redirect(url_for('main.report_form'))
        return f(*args, **kwargs)
    return decorated_function

def professional_login_required(f):
    """Decommissioned. Technician self-service portal has been eradicated; resolution is locked down to Admin/Higher Authority."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error='Technician portal access has been decommissioned. Higher Authority / Admin access required.', status=403)
        flash('Technician portal access has been decommissioned. Higher Authority / Admin access required.', 'error')
        return redirect(url_for('auth.login'))
    return decorated_function

# Clean up technician RBAC decorator alias
technician_required = professional_login_required

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

def supervisor_required(f):
    """
    Decorator to require Supervisor or Higher Authority access.
    Allowed roles: SUPERVISOR, SUPER_ADMIN, or users with is_supervisor / is_admin / is_super_admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and not session.get('is_super_admin'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Authentication required. Please log in.', status=401)
            flash('Supervisor access required. Please log in.', 'error')
            return redirect(url_for('auth.login'))

        user = _get_authenticated_user()

        from .models import User
        is_authorized = False
        if session.get('is_super_admin'):
            is_authorized = True
        elif user and (user.is_supervisor or user.is_super_admin or user.is_admin):
            is_authorized = True
        elif session.get('is_admin') or str(session.get('user_role') or '').upper() in [getattr(User, 'ROLE_SUPERVISOR', 'SUPERVISOR'), getattr(User, 'ROLE_SUPER_ADMIN', 'SUPER_ADMIN'), 'ADMIN', 'SUPERVISOR']:
            is_authorized = True

        if not is_authorized:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return api_response(success=False, error='Supervisor privileges required.', status=403)
            flash('Supervisor privileges required to access this workspace.', 'error')
            return redirect(url_for('main.report_form'))

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
            current_user_id = session.get('user_id')
            if not current_user_id:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                    return api_response(success=False, error='Authentication required.', status=401)
                return redirect(url_for('auth.login'))

            # 2. Extract record ID from route parameters (or request payload)
            record_id = kwargs.get(id_param) or (request.view_args.get(id_param) if request.view_args else None)
            if not record_id:
                return api_response(success=False, error=f'Missing parameter {id_param}', status=400)

            # 3. Retrieve target record from database
            from . import db
            try:
                record = db.session.get(model_class, record_id)
            except Exception:
                if hasattr(model_class, 'query') and hasattr(model_class.query, 'filter_by'):
                    record = model_class.query.filter_by(id=record_id).first()
                elif hasattr(model_class, 'query') and hasattr(model_class.query, 'get'):
                    record = model_class.query.get(record_id)
                else:
                    record = None
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
