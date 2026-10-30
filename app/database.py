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

        # Ensure profile_picture column exists on professionals table
        try:
            inspector = sqlalchemy.inspect(db.engine)
            if inspector.has_table('professionals'):
                columns = [c['name'] for c in inspector.get_columns('professionals')]
                if 'profile_picture' not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(sqlalchemy.text("ALTER TABLE professionals ADD COLUMN profile_picture TEXT;"))
                        conn.commit()
                    logger.info("Added profile_picture column to professionals table.")
            
            # Ensure Ghost Protocol columns exist on room_bookings
            if inspector.has_table('room_bookings'):
                rb_columns = [c['name'] for c in inspector.get_columns('room_bookings')]
                with db.engine.connect() as conn:
                    if 'checked_in' not in rb_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE room_bookings ADD COLUMN checked_in BOOLEAN DEFAULT FALSE;"))
                        logger.info("Added checked_in column to room_bookings table.")
                    if 'checked_in_at' not in rb_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE room_bookings ADD COLUMN checked_in_at TIMESTAMP;"))
                        logger.info("Added checked_in_at column to room_bookings table.")
                    conn.commit()

            # Ensure Ghost Protocol columns exist on adhoc_bookings
            if inspector.has_table('adhoc_bookings'):
                ah_columns = [c['name'] for c in inspector.get_columns('adhoc_bookings')]
                with db.engine.connect() as conn:
                    if 'checked_in' not in ah_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE adhoc_bookings ADD COLUMN checked_in BOOLEAN DEFAULT FALSE;"))
                        logger.info("Added checked_in column to adhoc_bookings table.")
                    if 'checked_in_at' not in ah_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE adhoc_bookings ADD COLUMN checked_in_at TIMESTAMP;"))
                        logger.info("Added checked_in_at column to adhoc_bookings table.")
                    conn.commit()

            # Ensure 3-Strike Accountability columns exist on users table
            if inspector.has_table('users'):
                u_columns = [c['name'] for c in inspector.get_columns('users')]
                with db.engine.connect() as conn:
                    if 'adhoc_suspended_until' not in u_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN adhoc_suspended_until TIMESTAMP;"))
                        logger.info("Added adhoc_suspended_until column to users table.")
                    if 'adhoc_suspension_reason' not in u_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN adhoc_suspension_reason VARCHAR(255);"))
                        logger.info("Added adhoc_suspension_reason column to users table.")
                    if 'designation' not in u_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN designation VARCHAR(100);"))
                        logger.info("Added designation column to users table.")
                    if 'is_active' not in u_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))
                        logger.info("Added is_active column to users table.")
                    conn.commit()

            # Ensure noshow_strikes table exists
            if not inspector.has_table('noshow_strikes'):
                db.create_all()
                logger.info("Created noshow_strikes table.")

            # Ensure schedule_submissions table exists
            if not inspector.has_table('schedule_submissions'):
                db.create_all()
                logger.info("Created schedule_submissions table.")

            # Ensure audit_logs table exists and has all required columns
            if not inspector.has_table('audit_logs'):
                db.create_all()
                logger.info("Created audit_logs table.")
            else:
                a_columns = [c['name'] for c in inspector.get_columns('audit_logs')]
                with db.engine.connect() as conn:
                    if 'ticket_id' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN ticket_id INTEGER;"))
                        logger.info("Added ticket_id column to audit_logs table.")
                    if 'performed_by_id' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN performed_by_id INTEGER;"))
                        logger.info("Added performed_by_id column to audit_logs table.")
                    if 'timestamp' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN timestamp TIMESTAMP;"))
                        logger.info("Added timestamp column to audit_logs table.")
                    if 'user_id' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN user_id INTEGER;"))
                        logger.info("Added user_id column to audit_logs table.")
                    if 'target_type' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN target_type VARCHAR(50);"))
                        logger.info("Added target_type column to audit_logs table.")
                    if 'target_id' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN target_id INTEGER;"))
                        logger.info("Added target_id column to audit_logs table.")
                    if 'created_at' not in a_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE audit_logs ADD COLUMN created_at TIMESTAMP;"))
                        logger.info("Added created_at column to audit_logs table.")
                    conn.commit()

            # Ensure Supervisor Verification columns exist on tickets table
            if inspector.has_table('tickets'):
                t_columns = [c['name'] for c in inspector.get_columns('tickets')]
                with db.engine.connect() as conn:
                    if 'assigned_vendor_or_tech_name' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN assigned_vendor_or_tech_name VARCHAR(150);"))
                        logger.info("Added assigned_vendor_or_tech_name column to tickets table.")
                    if 'verified_by_id' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN verified_by_id INTEGER;"))
                        logger.info("Added verified_by_id column to tickets table.")
                    if 'proof_image_url' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN proof_image_url VARCHAR(500);"))
                        logger.info("Added proof_image_url column to tickets table.")
                    if 'proof_of_completion_url' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN proof_of_completion_url VARCHAR(500);"))
                        logger.info("Added proof_of_completion_url column to tickets table.")
                    if 'resolution_notes' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN resolution_notes TEXT;"))
                        logger.info("Added resolution_notes column to tickets table.")
                    if 'resolved_at' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN resolved_at TIMESTAMP;"))
                        logger.info("Added resolved_at column to tickets table.")
                    if 'completion_photo_filename' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN completion_photo_filename VARCHAR(255);"))
                        logger.info("Added completion_photo_filename column to tickets table.")
                    if 'job_completed_at' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN job_completed_at TIMESTAMP;"))
                        logger.info("Added job_completed_at column to tickets table.")
                    if 'fixed_at' not in t_columns:
                        conn.execute(sqlalchemy.text("ALTER TABLE tickets ADD COLUMN fixed_at TIMESTAMP;"))
                        logger.info("Added fixed_at column to tickets table.")
                    conn.commit()
        except Exception as e:
            logger.warning(f"Could not verify schema migrations: {e}")

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

        # 3. Verify default professional (Bottle Singh)
        from .models import Professional
        try:
            bottle_prof = Professional.query.filter_by(username='bottlesingh#pro').first()
            if not bottle_prof:
                bottle_prof = Professional(
                    name='Bottle Singh',
                    username='bottlesingh#pro',
                    email='bottle.singh@fixlink.com',
                    phone='2424242424',
                    category='it_technician',
                    is_active=True
                )
                bottle_prof.set_password('tester456!')
                db.session.add(bottle_prof)
                db.session.commit()
                logger.info('Default professional created: Bottle Singh (bottlesingh#pro)')
            else:
                if not bottle_prof.check_password('tester456!'):
                    bottle_prof.set_password('tester456!')
                    db.session.commit()
                    logger.info('Updated Bottle Singh password to tester456!')
        except Exception as e:
            logger.error(f"Default professional creation check failed: {str(e)}")
            db.session.rollback()

        # 4. Verify Developer / Super Admin account (Om Mahadik)
        try:
            om_user = User.query.filter(db.func.lower(User.email) == 'om.mahadik@mitwpu.edu.in').first()
            if not om_user:
                om_user = User(
                    name='Om Mahadik',
                    email='om.mahadik@mitwpu.edu.in',
                    role=User.ROLE_ADMIN,
                    is_admin=True,
                    is_verified=True
                )
                om_user.set_password('omni12345')
                db.session.add(om_user)
                db.session.commit()
                logger.info('Developer/Super Admin account created: om.mahadik@mitwpu.edu.in')
            else:
                updated = False
                if not om_user.is_admin:
                    om_user.is_admin = True
                    updated = True
                if not om_user.is_verified:
                    om_user.is_verified = True
                    updated = True
                if not om_user.check_password('omni12345'):
                    om_user.set_password('omni12345')
                    updated = True
                if updated:
                    db.session.commit()
                    logger.info('Developer/Super Admin account credentials verified & synchronized.')
        except Exception as e:
            logger.error(f"Developer account check failed: {str(e)}")
            db.session.rollback()

        # 5. Verify Developer / Super Admin account (Taha Piplodwala)
        try:
            taha_user = User.query.filter(db.func.lower(User.email) == 'taha.piplodwala@mitwpu.edu.in').first()
            if not taha_user:
                taha_user = User(
                    name='Taha Piplodwala',
                    email='taha.piplodwala@mitwpu.edu.in',
                    role=User.ROLE_ADMIN,
                    is_admin=True,
                    is_verified=True
                )
                taha_user.set_password('Taha10vesgono!')
                db.session.add(taha_user)
                db.session.commit()
                logger.info('Developer/Super Admin account created: taha.piplodwala@mitwpu.edu.in')
            else:
                updated = False
                if not taha_user.is_admin:
                    taha_user.is_admin = True
                    updated = True
                if not taha_user.is_verified:
                    taha_user.is_verified = True
                    updated = True
                if not taha_user.check_password('Taha10vesgono!'):
                    taha_user.set_password('Taha10vesgono!')
                    updated = True
                if updated:
                    db.session.commit()
                    logger.info('Developer/Super Admin account credentials verified & synchronized for Taha Piplodwala.')
        except Exception as e:
            logger.error(f"Taha developer account check failed: {str(e)}")
            db.session.rollback()
