"""
FixLink Application Services Package
Centralized business logic layer decoupled from route handlers and database models.
"""
from .qr_service import (
    generate_qr_code,
    generate_qr_bytes,
    get_room_report_url,
    save_room_qr_code
)
from .map_service import (
    get_floor_svg,
    get_cached_floor_data,
    invalidate_floor_cache,
    invalidate_all_map_cache
)
from .realtime_service import (
    get_pusher,
    trigger_event,
    notify_professional_assigned,
    notify_admin_job_started,
    notify_admin_job_completed,
    notify_admin_job_cancelled,
    notify_admin_help_requested,
    notify_help_request_approved,
    emit_room_status_change,
    emit_faculty_nudge
)
from .email_service import (
    send_ticket_email,
    send_verification_email,
    send_password_reset_email,
    send_sla_escalation_email,
    send_web_push
)
from .sla_service import (
    get_pending_batches_sla_status,
    trigger_department_sla_escalation,
    superadmin_override_bulk_approve
)
from .analytics_service import (
    get_technician_efficiency,
    get_system_trends,
    get_critical_assets
)
from .spam_service import (
    detect_report_spam,
    get_user_daily_reports_count,
    is_daily_report_limit_exceeded,
    apply_spam_strike_to_user
)

__all__ = [
    'generate_qr_code',
    'generate_qr_bytes',
    'get_room_report_url',
    'save_room_qr_code',
    'get_floor_svg',
    'get_cached_floor_data',
    'invalidate_floor_cache',
    'invalidate_all_map_cache',
    'get_pusher',
    'trigger_event',
    'notify_professional_assigned',
    'notify_admin_job_started',
    'notify_admin_job_completed',
    'notify_admin_job_cancelled',
    'notify_admin_help_requested',
    'notify_help_request_approved',
    'emit_room_status_change',
    'emit_faculty_nudge',
    'send_ticket_email',
    'send_verification_email',
    'send_password_reset_email',
    'send_sla_escalation_email',
    'send_web_push',
    'get_pending_batches_sla_status',
    'trigger_department_sla_escalation',
    'superadmin_override_bulk_approve',
    'get_technician_efficiency',
    'get_system_trends',
    'get_critical_assets',
    'detect_report_spam',
    'get_user_daily_reports_count',
    'is_daily_report_limit_exceeded',
    'apply_spam_strike_to_user',
]
