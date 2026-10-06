"""
Onboarding & Legal Compliance Clickwrap Blueprint for FixLink.
Provides mandatory interstitial terms acceptance gates and anti-tamper endpoints.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app import db, csrf
from app.models import User

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')


def get_current_user():
    """Helper to safely retrieve the current logged-in user."""
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    super_admin_email = session.get('super_admin_email')
    if super_admin_email:
        return User.query.filter_by(email=super_admin_email).first()
    return None


def get_dashboard_redirect(user):
    """Direct user to their designated portal dashboard upon compliance clearance."""
    if not user:
        return redirect(url_for('auth.login'))
    if getattr(user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))
    elif getattr(user, 'role', '') == 'faculty':
        return redirect(url_for('faculty.dashboard'))
    else:
        return redirect(url_for('main.report_form'))


@onboarding_bp.route('/terms', methods=['GET', 'POST'])
def terms():
    """Mandatory Interstitial Clickwrap Gate for Ghost Protocol & Terms of Service."""
    user = get_current_user()
    if not user:
        flash('Authentication required. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    # If already compliant, bypass straight to dashboard
    if user.has_accepted_terms:
        return get_dashboard_redirect(user)

    if request.method == 'POST':
        return process_acceptance(user)

    return render_template('onboarding_terms.html', user=user)


@onboarding_bp.route('/accept', methods=['POST'])
@csrf.exempt
def accept():
    """Dedicated endpoint to process terms acceptance with race-condition rollback."""
    user = get_current_user()
    if not user:
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'unauthorized', 'message': 'Authentication required.'}), 401
        flash('Authentication required. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    return process_acceptance(user)


def process_acceptance(user):
    """Atomic acceptance handler with OperationalError transaction rollback."""
    accepted = request.form.get('accept_terms')
    if not accepted:
        flash('You must check the agreement box to accept the terms before continuing.', 'error')
        return redirect(url_for('onboarding.terms'))

    try:
        user.has_accepted_terms = True
        db.session.commit()
        logger.info(f"User {user.email} (ID: {user.id}) successfully accepted Terms of Service & Ghost Protocol.")
        flash('Terms of Service and Ghost Protocol successfully acknowledged.', 'success')
        return get_dashboard_redirect(user)
    except OperationalError as oe:
        db.session.rollback()
        logger.error(f"OperationalError during terms acceptance for user {user.id}: {oe}")
        flash('Database is temporarily busy. Please re-submit your acceptance.', 'error')
        return redirect(url_for('onboarding.terms'))
    except SQLAlchemyError as se:
        db.session.rollback()
        logger.error(f"SQLAlchemyError during terms acceptance for user {user.id}: {se}")
        flash('A database synchronization issue occurred. Please try again.', 'error')
        return redirect(url_for('onboarding.terms'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during terms acceptance for user {user.id}: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('onboarding.terms'))
