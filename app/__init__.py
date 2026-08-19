"""
MIT-WPU Vyas Smart-Room Maintenance Tracker
Flask Application Factory
"""
import os
import secrets
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Core instances
db = SQLAlchemy()
csrf = CSRFProtect()

try:
    from flask_migrate import Migrate
    migrate = Migrate()
except ImportError:
    migrate = None

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Application factory pattern for creating Flask app."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    if config_name == 'testing' or os.environ.get('TESTING') == 'True':
        app.config['TESTING'] = True
    
    # Configuration — all secrets come from .env
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('VERCEL'):
            # Enforce secret key on Vercel for session stability
            raise RuntimeError('SECRET_KEY must be set in Vercel Environment Variables for session stability.')
        
        secret_key = secrets.token_hex(32)
        logger.warning(
            'SECRET_KEY is not set in environment. A temporary random key has been generated. '
            'Sessions will not persist across server restarts. Set SECRET_KEY in your .env file.'
        )
    app.config['SECRET_KEY'] = secret_key

    # Session security (applied to ALL environments)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
    )

    # Vercel-specific session security
    if os.environ.get('VERCEL'):
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            WTF_CSRF_SSL_STRICT=False,       # Let Vercel handle SSL termination
            WTF_CSRF_TIME_LIMIT=None,        # No timeout for serverless cold starts
            WTF_CSRF_ENABLED=True,           # Explicitly enabled
        )
        # Trust Vercel's proxy headers (Vercel uses multiple layers of proxy)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=2, x_host=2, x_prefix=2)
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Check if we're in testing mode
        if config_name == 'testing' or os.environ.get('TESTING') == 'True':
            database_url = 'sqlite:///:memory:'
            logger.info('Using in-memory SQLite for testing.')
        else:
            raise RuntimeError(
                'DATABASE_URL is not set. A persistent PostgreSQL (Supabase) '
                'connection is required for the application to start.'
            )
    
    # Supabase Connection Hardening (especially for Vercel/SSL)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    # Add SSL mode if on Vercel and it's missing
    if os.environ.get('VERCEL') and 'sslmode=' not in database_url:
        separator = '&' if '?' in database_url else '?'
        database_url += f'{separator}sslmode=require'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # PostgreSQL connection pool settings
    if database_url.startswith('postgresql'):
        if os.environ.get('VERCEL'):
            # Vercel is serverless — use NullPool to avoid stale connections
            from sqlalchemy.pool import NullPool
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'poolclass': NullPool,
                'pool_pre_ping': True,
            }
        else:
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 5,
                'pool_recycle': 300,
                'pool_pre_ping': True,
            }
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists (Skip on Vercel read-only filesystem)
    if not os.environ.get('VERCEL'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    if migrate:
        migrate.init_app(app, db)
    
    # Initialize Cache
    from .cache import init_cache
    init_cache(app)
    
    # Security: CSRF Protection
    csrf.init_app(app)
    
    # Security: Rate Limiting (Optional)
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=["1000 per day", "100 per hour"],
            storage_uri="memory://",
        )
    except ImportError:
        limiter = None
    
    # Initialize database and run migrations (Selective on Vercel)
    from .database import init_db
    init_db(app)

    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.admin import admin_bp
    from .blueprints.auth import auth_bp
    from .blueprints.professional import professional_bp
    from .blueprints.superadmin import superadmin_bp
    from .blueprints.faculty.routes import faculty_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    app.register_blueprint(professional_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(faculty_bp, url_prefix='/faculty')

    # Pusher is initialized lazily in realtime.py
    
    # Start background scheduler for automated alerts (disabled on Vercel)
    if not os.environ.get('VERCEL'):
        from .scheduler import start_scheduler
        start_scheduler(app)
    else:
        logger.info("Running on Vercel: Background scheduler disabled.")
    
    # Global Session Refresh Hook
    # NOTE: The database queries in @app.before_request were removed to optimize 
    # Vercel serverless latency. We now fully trust the cryptographically signed 
    # Flask session cookies for user roles and emails, which avoids opening a 
    # costly PostgreSQL connection on every single request.
    
    # Global Template Context
    @app.context_processor
    def inject_globals():
        from .blueprints.superadmin.routes import SUPER_ADMIN_EMAIL
        return dict(
            SUPER_ADMIN_EMAIL=SUPER_ADMIN_EMAIL,
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
    
    return app
