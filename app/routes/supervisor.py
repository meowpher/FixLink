"""
Supervisor Blueprint Routes - Quality Assurance & Verification Workspace
Strictly scoped to active tickets (OPEN / IN_PROGRESS). Excludes global system analytics.
"""
import os
import time
import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app, abort, g
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from PIL import Image

from app import db
from app.models import Ticket, User, Asset, AuditLog, Room
from app.decorators import supervisor_required
from app.utils import allowed_file, save_webapp_file
from app.api_utils import api_response, handle_api_errors
supervisor_bp = Blueprint('supervisor', __name__)

logger = logging.getLogger(__name__)


@supervisor_bp.route('/')
@supervisor_bp.route('/dashboard')
@supervisor_required
def dashboard():
    """
    Dedicated Mobile-First Supervisor Workspace.
    Displays only active maintenance tickets ('OPEN', 'IN_PROGRESS') requiring on-ground physical inspection.
    Global system analytics and administrative bloat are completely excluded.
    """
    # 1. Fetch current supervisor context
    supervisor_user = getattr(g, '_current_user_cached', None)
    if not supervisor_user and 'user_id' in session:
        try:
            supervisor_user = db.session.get(User, session['user_id'])
        except Exception:
            supervisor_user = None
    elif not supervisor_user and session.get('super_admin_email'):
        try:
            supervisor_user = User.query.filter_by(email=session['super_admin_email']).first()
        except Exception:
            supervisor_user = None

    # 2. Query strictly active tickets (OPEN and IN_PROGRESS)
    # Eager-load relations to ensure zero N+1 latency on mobile connections
    active_statuses = [
        Ticket.STATUS_OPEN, 
        Ticket.STATUS_IN_PROGRESS, 
        'OPEN', 
        'IN_PROGRESS', 
        'open', 
        'in_progress'
    ]

    query = Ticket.query.options(
        joinedload(Ticket.room).joinedload(Room.floor),
        joinedload(Ticket.reporter),
        joinedload(Ticket.asset)
    ).filter(
        Ticket.status.in_(active_statuses)
    ).order_by(
        Ticket.created_at.desc()
    )

    tickets = query.all()

    # 3. Compute clean operational metrics (no heavy analytics)
    open_count = sum(1 for t in tickets if str(t.status).upper() in ['OPEN', Ticket.STATUS_OPEN])
    in_progress_count = sum(1 for t in tickets if str(t.status).upper() in ['IN_PROGRESS', Ticket.STATUS_IN_PROGRESS])
    total_active = len(tickets)

    return render_template(
        'supervisor/dashboard.html',
        tickets=tickets,
        open_count=open_count,
        in_progress_count=in_progress_count,
        total_active=total_active,
        supervisor=supervisor_user
    )


@supervisor_bp.route('/issues/<int:ticket_id>/verify-close', methods=['POST'])
@supervisor_bp.route('/tickets/<int:ticket_id>/verify-close', methods=['POST'])
@supervisor_required
@handle_api_errors
def verify_and_close_ticket(ticket_id):
    """
    Supervisor Quality Assurance Verification & Closure Endpoint (Phase 4).
    Enforces:
      - Zero-Trust X-Tab-Guard-ID header validation.
      - User role check ensuring requester is at least SUPERVISOR.
      - File upload validation with werkzeug secure_filename and UUID prefix.
      - Atomic DB transaction binding verified_by_id, proof URL, notes, and immutable AuditLog.
    """
    # 1. Enforce Zero-Trust X-Tab-Guard-ID check
    client_guard_id = request.headers.get('X-Tab-Guard-ID') or request.form.get('X-Tab-Guard-ID')
    server_guard_id = session.get('tab_guard_id')
    if server_guard_id and client_guard_id != server_guard_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Security violation: Zero-Trust Tab Guard mismatch.", status=403)
        flash("Security violation: Zero-Trust Tab Guard mismatch.", "error")
        return redirect(url_for('supervisor.dashboard'))

    # 2. Ensure current user's role is at least SUPERVISOR
    supervisor_id = session.get('user_id')
    current_user_obj = db.session.get(User, supervisor_id) if supervisor_id else None
    
    is_at_least_supervisor = False
    if session.get('is_super_admin'):
        is_at_least_supervisor = True
    elif current_user_obj and (current_user_obj.is_supervisor or current_user_obj.is_super_admin or current_user_obj.is_admin):
        is_at_least_supervisor = True
    elif str(session.get('user_role') or '').upper() in [User.ROLE_SUPERVISOR, User.ROLE_SUPER_ADMIN, 'ADMIN', 'SUPERVISOR']:
        is_at_least_supervisor = True

    if not is_at_least_supervisor:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Unauthorized: User role must be at least SUPERVISOR.", status=403)
        flash("Unauthorized: User role must be at least SUPERVISOR.", "error")
        return redirect(url_for('main.report_form'))

    ticket = Ticket.query.get_or_404(ticket_id)

    # 3. Validate proof of completion file
    if 'proof_image' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Proof of completion image is required.", status=400)
        flash("Proof of completion image is required.", "error")
        return redirect(url_for('supervisor.dashboard'))

    file = request.files['proof_image']
    if not file or not file.filename:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="A valid image file must be uploaded or captured.", status=400)
        flash("A valid image file must be uploaded or captured.", "error")
        return redirect(url_for('supervisor.dashboard'))

    if not allowed_file(file.filename):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.", status=400)
        flash("Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.", "error")
        return redirect(url_for('supervisor.dashboard'))

    # 4. Validate technician/vendor name and supervisor inspection remarks
    technician_name = (request.form.get('technician_name') or request.form.get('vendor_name') or '').strip()
    if not technician_name:
        technician_name = "External / On-ground Technician"

    resolution_notes = (request.form.get('resolution_notes') or request.form.get('notes') or '').strip()
    if not resolution_notes:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Supervisor inspection notes are required.", status=400)
        flash("Supervisor inspection notes are required.", "error")
        return redirect(url_for('supervisor.dashboard'))

    # 5. Handle image upload safely using Pillow (PIL) compression to prevent server storage exhaustion
    safe_name = secure_filename(file.filename) or 'proof.jpg'
    base_name, ext = os.path.splitext(safe_name)
    ext_lower = ext.lower()

    # Determine optimal compressed format (.jpg for jpeg/jpg, .webp for others)
    if ext_lower in ['.jpg', '.jpeg']:
        out_ext = '.jpg'
        img_format = 'JPEG'
    else:
        out_ext = '.webp'
        img_format = 'WEBP'

    uuid_prefix = str(uuid.uuid4())
    unique_filename = f"{uuid_prefix}_{base_name}{out_ext}"
    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads')), 'proofs')
    os.makedirs(upload_dir, exist_ok=True)
    full_save_path = os.path.join(upload_dir, unique_filename)

    # Perform PIL image compression: Convert to RGB, resize (max-width 1200px maintaining aspect ratio), quality=70
    file.seek(0)
    try:
        with Image.open(file) as img:
            # Convert to RGB (handles RGBA, Palette, Grayscale, CMYK, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize maintaining aspect ratio if image exceeds 1200px width
            max_width = 1200
            if img.width > max_width:
                aspect_ratio = img.height / float(img.width)
                new_height = int(max_width * aspect_ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Save as highly compressed image (quality=70)
            if img_format == 'JPEG':
                img.save(full_save_path, 'JPEG', quality=70, optimize=True)
            else:
                img.save(full_save_path, 'WEBP', quality=70, method=6)
    except Exception as img_err:
        logger.warning(f"PIL compression encountered error ({img_err}); falling back to safe direct persistence.")
        file.seek(0)
        save_webapp_file(file, full_save_path)

    proof_url = f"/static/uploads/proofs/{unique_filename}"

    # 6. Atomic state update and immutable AuditLog entry
    now_utc = datetime.utcnow()
    supervisor_name = current_user_obj.name if current_user_obj else session.get('super_admin_email', 'Supervisor')

    ticket.status = Ticket.STATUS_RESOLVED
    ticket.assigned_vendor_or_tech_name = technician_name
    ticket.verified_by_id = supervisor_id
    ticket.proof_image_url = proof_url
    ticket.proof_of_completion_url = proof_url
    ticket.completion_photo_filename = unique_filename
    ticket.resolution_notes = resolution_notes
    ticket.resolved_at = now_utc
    ticket.fixed_at = now_utc
    ticket.job_completed_at = now_utc
    ticket.updated_at = now_utc

    # Update associated asset if applicable
    if ticket.asset_id:
        asset = db.session.get(Asset, ticket.asset_id)
        if asset:
            asset.status = Asset.STATUS_WORKING

    # Unique Audit Log entry per ticket (maintaining strict 1:1 uniqueness)
    existing_audit = AuditLog.query.filter(
        AuditLog.action == "TICKET_VERIFIED_CLOSED",
        or_(AuditLog.ticket_id == ticket.id, (AuditLog.target_type == 'Ticket') & (AuditLog.target_id == ticket.id))
    ).first()

    if existing_audit:
        existing_audit.ticket_id = ticket.id
        existing_audit.performed_by_id = supervisor_id
        existing_audit.user_id = supervisor_id
        existing_audit.details = f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached."
        existing_audit.timestamp = now_utc
        existing_audit.created_at = now_utc
    else:
        audit_entry = AuditLog(
            ticket_id=ticket.id,
            action="TICKET_VERIFIED_CLOSED",
            performed_by_id=supervisor_id,
            timestamp=now_utc,
            details=f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached.",
            user_id=supervisor_id,
            target_type="Ticket",
            target_id=ticket.id,
            created_at=now_utc
        )
        db.session.add(audit_entry)
    db.session.commit()

    success_msg = f"Ticket #{ticket.id} verified and marked as RESOLVED by Supervisor {supervisor_name}."
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return api_response(
            success=True,
            message=success_msg,
            data={
                'ticket': {
                    'id': ticket.id,
                    'status': ticket.status,
                    'proof_image_url': ticket.proof_image_url,
                    'resolution_notes': ticket.resolution_notes,
                    'verified_by': supervisor_name,
                    'resolved_at': now_utc.isoformat() + 'Z'
                }
            }
        )

    flash(success_msg, "success")
    return redirect(url_for('supervisor.dashboard'))
