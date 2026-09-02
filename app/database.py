"""
Database initialization and migration logic for FixLink.
Provides a central location for custom table/column checks and initial data setup.
"""
import os
import logging
from . import db

logger = logging.getLogger(__name__)

def init_db(app):
    """
    Perform database initialization tasks safely adhering to Rule 4 of Rules.md:
    1. Check table existence using sqlalchemy.inspect(db.engine).has_table.
    2. Auto-create missing tables and trigger auto-seeding via init_data.py.
    3. Ensure admin users exist.
    """
    with app.app_context():
        # Skip setup logic in Testing mode (DB managed by pytest fixture)
        if app.config.get('TESTING') or os.environ.get('TESTING') == 'True':
            logger.info('Skipping database setup in Testing environment.')
            return

        # 0. Ensure models are registered with SQLAlchemy
        from . import models
        import sqlalchemy

        # 1. Inspect database schema safely before issuing queries
        try:
            inspector = sqlalchemy.inspect(db.engine)
            has_buildings = inspector.has_table('buildings')
            has_users = inspector.has_table('users')
        except Exception as e:
            logger.warning(f"Database inspector check failed: {e}. Running db.create_all().")
            has_buildings = False
            has_users = False

        if not has_buildings or not has_users:
            logger.info("Database tables missing. Executing db.create_all() inside app_context()...")
            db.create_all()
            try:
                from scripts.init_data import create_vyas_data
                logger.info("Auto-seeding Vyas architecture, 8 floors, and rooms...")
                create_vyas_data(app, interactive=False)
            except Exception as e:
                logger.error(f"Auto-seeding Vyas data failed: {str(e)}")
        else:
            # Tables exist: check if Vyas building is populated
            from .models import Building
            try:
                if not Building.query.filter_by(name='Vyas').first():
                    from scripts.init_data import create_vyas_data
                    logger.info("Vyas building record missing. Auto-seeding...")
                    create_vyas_data(app, interactive=False)
            except Exception as e:
                logger.error(f"Building query check failed: {str(e)}")

        # 2. Verify default admin user
        from .models import User
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if admin_email and admin_password:
            try:
                if not User.query.filter_by(email=admin_email).first():
                    admin_user = User(
                        name='Admin',
                        email=admin_email,
                        role=User.ROLE_ADMIN,
                        is_admin=True,
                        is_verified=True
                    )
                    admin_user.set_password(admin_password)
                    db.session.add(admin_user)
                    db.session.commit()
                    logger.info(f'Default admin user created: {admin_email}')
            except Exception as e:
                logger.error(f"Admin user creation check failed: {str(e)}")
