"""
MIT-WPU Vyas Smart-Room Maintenance Tracker
Flask Application Factory
"""
from datetime import timedelta
import os
import secrets
import logging
from flask import Flask, session, request, redirect, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Core instances
db = SQLAlchemy()
csrf = CSRFProtect()

try:
    from flask_migrate import Migrate  # type: ignore[import-untyped]
    migrate = Migrate()
except ImportError:
    migrate = None

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Root User / Super Admin hardcoded authorization list
SUPER_ADMIN_EMAILS = [
    "taha.piplodwala@mitwpu.edu.in",
    "om.mahadik@mitwpu.edu.in"
]


def create_app(config_name=None):
    """Application factory pattern for creating Flask app."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    app.config['SUPER_ADMIN_EMAILS'] = SUPER_ADMIN_EMAILS

    if config_name == 'testing' or os.environ.get('TESTING') == 'True':
        app.config['TESTING'] = True

    # Configuration — all secrets come from .env
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = os.environ.get('FLASK_SECRET_KEY', 'fixlink-production-fallback-key-secret-987234')
        logger.warning(
            'SECRET_KEY is not set in environment. Using fallback key. '
            'Sessions will not persist across server restarts. Set SECRET_KEY in your .env or Vercel Environment Variables.'
        )
    app.config['SECRET_KEY'] = secret_key

    # Phase 1: Cookie & Session Lockdown
    # Determine if Secure cookie flag should be set (enabled in production/HTTPS, disabled in local HTTP development)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),    # Strict 2-hour idle session expiration
        WTF_CSRF_TIME_LIMIT=None,                        # No timeout to prevent stale form issues
        WTF_CSRF_SSL_STRICT=False,                       # Disable strict referer checking for local/proxy environments
        WTF_CSRF_ENABLED=True,                           # Explicitly enabled
    )

    # Vercel / Reverse Proxy headers support
    if os.environ.get('VERCEL'):
        # Trust Vercel's proxy headers (Vercel uses multiple layers of proxy)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=2, x_host=2, x_prefix=2)

    if config_name == 'testing' or os.environ.get('TESTING') == 'True':
        database_url = 'sqlite:///:memory:'
        logger.info('Using in-memory SQLite for testing.')
    else:
        # 1. Fetch URI via DATABASE_URL or SQLALCHEMY_DATABASE_URI
        database_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
        if not database_url:
            raise RuntimeError(
                'DATABASE_URL is not set. A persistent PostgreSQL (Supabase) '
                'connection is required for the application to start.'
            )
        # 2. Sanitize string: strip whitespace, quotes, and hidden newline characters
        database_url = database_url.strip().strip('"').strip("'")

    # 3. Fix SQLAlchemy dialect: If URI starts with postgres://, replace with postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    # Supabase connection pooler: Port 5432 is Session mode (hard-limited to 15 clients).
    # Port 6543 is Transaction mode (supports unlimited concurrent client requests).
    if 'pooler.supabase.com:5432' in database_url:
        logger.info("Routing Supabase pooler connection from Session port 5432 to Transaction port 6543.")
        database_url = database_url.replace('pooler.supabase.com:5432', 'pooler.supabase.com:6543')

    # 4. Enforce SSL: If connecting to a remote PostgreSQL host and sslmode is missing, append sslmode=require
    if database_url.startswith('postgresql') and 'localhost' not in database_url and '127.0.0.1' not in database_url:
        if 'sslmode=' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url += f'{separator}sslmode=require'

    # Automatic PostgreSQL Driver Fallback: test available DBAPI drivers
    if database_url.startswith(('postgresql://', 'postgres://', 'postgresql+')):
        import re
        base_pg_url = re.sub(r'^(postgresql|postgres)(\+[a-zA-Z0-9_-]+)?://', '', database_url)
        try:
            import psycopg2  # noqa: F401
            database_url = f'postgresql+psycopg2://{base_pg_url}'
            logger.info("PostgreSQL driver verified: psycopg2")
        except ImportError:
            try:
                import psycopg  # noqa: F401
                database_url = f'postgresql+psycopg://{base_pg_url}'
                logger.info("PostgreSQL driver verified: psycopg (v3)")
            except ImportError:
                try:
                    import pg8000  # noqa: F401
                    clean_url = re.sub(r'[?&]sslmode=[^&]+', '', base_pg_url)
                    if clean_url.endswith('?'):
                        clean_url = clean_url[:-1]
                    database_url = f'postgresql+pg8000://{clean_url}'
                    logger.info("PostgreSQL driver verified: pg8000")
                except ImportError:
                    logger.warning("No PostgreSQL driver found; retaining base postgresql:// scheme")
                    database_url = f'postgresql://{base_pg_url}'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 5. Serverless Pooling Hardening: Check if os.environ.get('VERCEL') == '1'
    if os.environ.get('VERCEL') == '1' or bool(os.environ.get('VERCEL')):
        from sqlalchemy.pool import NullPool
        engine_opts = {
            'poolclass': NullPool,
            'pool_pre_ping': True,
        }
        if database_url.startswith('postgresql+pg8000://'):
            engine_opts['connect_args'] = {'ssl_context': True}
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_opts
    else:
        if database_url.startswith(('postgresql', 'mysql')):
            connect_args = {'connect_timeout': 10}
            if database_url.startswith('postgresql'):
                connect_args.update({
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5,
                })
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
                'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 280)),  # 280s to stay below 300s cloud idle timeout
                'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
                'pool_pre_ping': True,  # Prevent connection timeouts and stale database drops
                'connect_args': connect_args,
            }

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Ensure upload directory exists (Skip on Vercel read-only filesystem)
    if not os.environ.get('VERCEL'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    if migrate:
        migrate.init_app(app, db)  # type: ignore[arg-type]

    # Initialize Cache
    from .cache import init_cache
    init_cache(app)

    # Security: CSRF Protection
    csrf.init_app(app)

    # Security: Rate Limiting (Optional)
    # try:
    # from flask_limiter import Limiter
    # from flask_limiter.util import get_remote_address
    # limiter = Limiter(
    # key_func=get_remote_address,
    # app=app,
    # default_limits=["1000 per day", "100 per hour"],
    # storage_uri="memory://",
    # )
    # except ImportError:
    # limiter = None
    limiter = None

    # Initialize database and run migrations (Skipped on Vercel to eliminate 16s+ cold-start timeouts)
    if not os.environ.get('VERCEL'):
        from .database import init_db
        init_db(app)
    else:
        logger.info('Running on Vercel: Database schema inspection and auto-seeding skipped for ultra-fast serverless cold start.')

    # Register blueprints from app.routes
    from .routes import (
        main_bp,
        admin_bp,
        auth_bp,
        superadmin_bp,
        faculty_bp,
        onboarding_bp,
        supervisor_bp,
        professional_bp
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
    app.register_blueprint(professional_bp)

    # In-memory Floor Plan SVG cache for instantaneous zero-latency template rendering
    _floor_svg_memory_cache = {}

    def get_floor_svg(level):
        lvl = str(level)
        if lvl not in _floor_svg_memory_cache:
            svg_file = os.path.join(app.root_path, 'static', 'svg_maps', f'VY{lvl}.svg')
            if not os.path.isfile(svg_file):
                svg_file = os.path.join(app.root_path, 'static', 'images', 'floors', f'VY{lvl}.svg')
            if os.path.isfile(svg_file):
                try:
                    with open(svg_file, 'r', encoding='utf-8') as f:
                        _floor_svg_memory_cache[lvl] = f.read()
                except Exception:
                    _floor_svg_memory_cache[lvl] = ''
            else:
                _floor_svg_memory_cache[lvl] = ''
        return _floor_svg_memory_cache.get(lvl, '')

    @app.context_processor
    def inject_floor_svg_processor():
        return dict(get_floor_svg=get_floor_svg)

    app.jinja_env.globals['get_floor_svg'] = get_floor_svg  # type: ignore[assignment]

    # Pusher is initialized lazily in realtime.py

    # Start background scheduler for automated alerts (disabled on Vercel)
    if not os.environ.get('VERCEL'):
        from .scheduler import start_scheduler
        start_scheduler(app)
    else:
        logger.info("Running on Vercel: Background scheduler disabled.")

    # Global Session Sanitizer & Lifetime Hook (Zero DB queries, purely in-memory)
    @app.before_request
    def sanitize_conflicting_session():
        # Enforce permanent session lifecycle so 2-hour idle timeout is applied
        session.permanent = True
        # Eradicate any legacy professional session keys
        if session.get('professional_id'):
            session.pop('professional_id', None)
            session.pop('professional_name', None)
            session.pop('professional_category', None)



    # Phase 2: Clickwrap Legal Compliance Middleware Interceptor
    @app.before_request
    def enforce_terms_compliance_interceptor():
        # Loophole Guard: If request.endpoint is None, immediately return to let Flask handle the 404 naturally.
        if request.endpoint is None:
            return None

        # Resolve authenticated user (via cached g or session)
        user = None
        user_id = session.get('user_id')
        if user_id and getattr(g, '_current_user_id', None) == user_id and getattr(g, '_current_user_cached', None) is not None:
            user = g._current_user_cached
        elif user_id:
            from .models import User
            try:
                user = db.session.get(User, user_id)
            except Exception as e:
                logger.warning(f"Database session get user failed ({e}), refreshing connection...")
                try:
                    db.session.rollback()
                    db.session.remove()
                    user = db.session.get(User, user_id)
                except Exception as inner_e:
                    logger.error(f"Failed to fetch user {user_id} after connection reset: {inner_e}")
                    user = None
        elif session.get('super_admin_email'):
            from .models import User
            try:
                user = User.query.filter_by(email=session['super_admin_email']).first()
            except Exception as e:
                logger.warning(f"Database session query superadmin failed ({e}), refreshing connection...")
                try:
                    db.session.rollback()
                    db.session.remove()
                    user = User.query.filter_by(email=session['super_admin_email']).first()
                except Exception as inner_e:
                    logger.error(f"Failed to fetch superadmin after connection reset: {inner_e}")
                    user = None

        if user:
            g._current_user_cached = user
            g._current_user_id = user.id
        else:
            g._current_user_cached = None
            g._current_user_id = None

        # Logic: If current_user.is_authenticated AND current_user.has_accepted_terms == False:
        is_authenticated = user is not None and getattr(user, 'is_authenticated', True)
        if is_authenticated and not getattr(user, 'has_accepted_terms', False):
            # Whitelist: static, logout, and your login/auth routes
            if request.endpoint.startswith('static') or \
               request.endpoint in {'static', 'logout', 'auth.logout', 'superadmin.logout', 'onboarding.terms', 'onboarding.accept'} or \
               request.endpoint.startswith('auth.') or \
               request.endpoint.startswith('onboarding.'):
                return None

            # API Trap: If the path starts with /api/, abort and return 403 Forbidden with JSON {"error": "terms_required", "redirect": "/logout"}
            if request.path.startswith('/api/'):
                return jsonify({
                    "error": "terms_required",
                    "redirect": "/logout"
                }), 403

            # Web Trap: If they bypassed the login form (e.g., via SSO), redirect them to a forced logout or dedicated terms page
            return redirect('/onboarding/terms')

        return None

    # Global Request & Security Headers Hook (Performance & Best Practices 100/100)
    import gzip
    @app.after_request
    def apply_performance_and_security_headers(response):
        # 1. Security Headers (Best Practices 100/100)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # 2. Static Asset & Page Caching (Performance 100/100 & BFCache Restoration)
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif request.path.startswith('/api/auth/status'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        else:
            # Overwrite any default 'no-store' headers to allow Back/Forward Cache (BFCache)
            # while still requiring revalidation on browser return
            current_cc = response.headers.get('Cache-Control', '')
            if not current_cc or 'no-store' in current_cc:
                response.headers['Cache-Control'] = 'private, no-cache, must-revalidate'

        # 3. Dynamic Gzip Compression Middleware (Performance 100/100)
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if (
            'gzip' in accept_encoding.lower()
            and 200 <= response.status_code < 300
            and 'Content-Encoding' not in response.headers
        ):
            content_type = response.headers.get('Content-Type', '').lower()
            compressible_types = ('text/', 'application/json', 'application/javascript', 'application/x-javascript', 'image/svg+xml', 'application/xml')
            if any(content_type.startswith(ct) for ct in compressible_types):
                try:
                    if response.direct_passthrough:
                        response.direct_passthrough = False
                    data = response.get_data()
                    if len(data) >= 200:
                        compressed_data = gzip.compress(data, compresslevel=6)
                        response.set_data(compressed_data)
                        response.headers['Content-Encoding'] = 'gzip'
                        response.headers['Content-Length'] = len(compressed_data)
                        response.headers['Vary'] = 'Accept-Encoding'
                except Exception:
                    pass

        return response

    # Global Template Context with G-Memoization
    from flask import g
    @app.context_processor
    def inject_globals():
        current_user_obj = None
        user_id = session.get('user_id')
        if user_id and getattr(g, '_current_user_id', None) == user_id and getattr(g, '_current_user_cached', None) is not None:
            current_user_obj = g._current_user_cached
        else:
            if user_id:
                from .models import User
                try:
                    current_user_obj = db.session.get(User, user_id)
                except Exception:
                    try:
                        db.session.rollback()
                        db.session.remove()
                        current_user_obj = db.session.get(User, user_id)
                    except Exception:
                        current_user_obj = None
            if not current_user_obj and session.get('super_admin_email'):
                from .models import User
                try:
                    current_user_obj = User.query.filter_by(email=session['super_admin_email']).first()
                except Exception:
                    try:
                        db.session.rollback()
                        db.session.remove()
                        current_user_obj = User.query.filter_by(email=session['super_admin_email']).first()
                    except Exception:
                        current_user_obj = None
                if not current_user_obj:
                    class SuperAdminUserProxy:
                        def __init__(self, email):
                            self.email = email
                            self.role = 'SUPER_ADMIN'
                            self.id = None
                            self.name = 'Super Admin'
                            self.has_accepted_terms = True
                            self.is_authenticated = True
                    current_user_obj = SuperAdminUserProxy(session['super_admin_email'])
            elif not current_user_obj and session.get('user_email'):
                from .models import User
                current_user_obj = User.query.filter_by(email=session['user_email']).first()
                if not current_user_obj:
                    class UserProxy:
                        def __init__(self, email):
                            self.email = email
                            self.role = 'ADMIN'
                            self.id = None
                            self.name = 'Admin'
                            self.has_accepted_terms = True
                            self.is_authenticated = True
                    current_user_obj = UserProxy(session['user_email'])
            if current_user_obj:
                g._current_user_cached = current_user_obj
                g._current_user_id = getattr(current_user_obj, 'id', None)

        return dict(
            SUPER_ADMIN_EMAIL=SUPER_ADMIN_EMAILS[0],
            SUPER_ADMIN_EMAILS=SUPER_ADMIN_EMAILS,
            current_user=current_user_obj,
            PUSHER_KEY=os.environ.get('PUSHER_KEY'),
            PUSHER_CLUSTER=os.environ.get('PUSHER_CLUSTER')
        )

    # Register Jinja filters
    @app.template_filter('ist')
    def format_ist(value, format='%b %d, %H:%M'):
        if value is None:
            return ""
        from datetime import timedelta
        # UTC to IST is +5:30
        ist_time = value + timedelta(hours=5, minutes=30)
        return ist_time.strftime(format)

    # Graceful CSRF Error Handler
    from flask_wtf.csrf import CSRFError
    from flask import request, jsonify, redirect, url_for, flash, render_template
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(f"CSRF validation failed: {e.description} for {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Session or security token expired. Please refresh the page.'}), 400
        flash('Your session expired or security token was invalid. Please try again.', 'warning')
        return redirect(request.referrer or url_for('auth.login'))

    # 404 Not Found Error Handler - Custom Infrastructure Zone Not Found
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Database resilience: catch dropped/stale connections and gracefully recover
    from sqlalchemy.exc import OperationalError, DBAPIError
    @app.errorhandler(OperationalError)
    @app.errorhandler(DBAPIError)
    @app.errorhandler(500)
    def handle_database_connection_error(e):
        original_exc = getattr(e, 'original_exception', e)
        is_db_err = isinstance(original_exc, (OperationalError, DBAPIError)) or 'server closed the connection' in str(e).lower()
        if is_db_err:
            logger.warning(f"Database connection error intercepted ({original_exc}). Evicting stale connection.")
            try:
                db.session.rollback()
                db.session.remove()
            except Exception:
                pass

            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Database connection refreshed. Please retry.'}), 503

            if request.method == 'GET':
                return redirect(request.url)

            flash('Database connection was refreshed. Please try again.', 'warning')
            return redirect(request.referrer or url_for('main.index'))

        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
        return ('Internal Server Error', 500)

    return app

