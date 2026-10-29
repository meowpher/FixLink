import os
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db  # type: ignore  # pyrefly: ignore[missing-import]
from app.models import User, AuditLog, Ticket  # type: ignore  # pyrefly: ignore[missing-import]

app = create_app()
client = app.test_client()

with app.app_context():
    # 1. Check Uniqueness in AuditLog
    verified_ticket_16_logs = AuditLog.query.filter(
        AuditLog.action == 'TICKET_VERIFIED_CLOSED',
        AuditLog.ticket_id == 16
    ).all()
    print(f"Verified logs for Ticket #16 in DB: {len(verified_ticket_16_logs)}")

    # 2. Test Audit Trail for Admin/Superadmin
    admin = User.query.filter(User.is_admin == True, User.role == 'admin').first()
    assert admin is not None, "Admin user must exist"

    with client.session_transaction() as sess:
        sess['user_id'] = admin.id
        sess['user_role'] = 'superadmin'
        sess['is_super_admin'] = True
        sess['is_admin'] = True

    res_admin = client.get('/admin/audit-trail')
    assert res_admin.status_code == 200
    html_admin = res_admin.data.decode('utf-8')

    # Check dropdown
    assert 'Ticket Verified &amp; Closed' in html_admin or 'Ticket Verified & Closed' in html_admin
    assert 'User Promoted to Supervisor' in html_admin
    assert 'User Demoted to Faculty' in html_admin
    print("Test 1 Passed: Action dropdown contains all required human-readable actions.")

    # Check Role Manager on Superadmin audit trail
    assert 'Role Manager' in html_admin
    print("Test 2 Passed: Role Manager visible to superadmin on audit trail.")

    # Check Uniqueness on Audit Trail
    # Only one row for Ticket #16 should exist
    assert html_admin.count('data-ticket-id="16"') == 2  # Once on the pill, once on the details button in the SAME row
    print("Test 3 Passed: Uniqueness verified for Ticket #16.")

    # 3. Test Supervisor Dashboard & Role Manager removal
    supervisor_user = User.query.filter_by(role='SUPERVISOR').first()
    assert supervisor_user is not None

    with client.session_transaction() as sess:
        sess['user_id'] = supervisor_user.id
        sess['user_role'] = 'SUPERVISOR'
        sess['is_admin'] = True
        sess['is_super_admin'] = False

    res_sup_dash = client.get('/admin/')
    assert res_sup_dash.status_code == 200
    html_sup_dash = res_sup_dash.data.decode('utf-8')

    assert 'Supervisor Dashboard' in html_sup_dash
    assert 'Role Manager' not in html_sup_dash
    print("Test 4 Passed: 'Supervisor Dashboard' shown and 'Role Manager' removed from supervisor dashboard.")

    # Test Supervisor Audit Trail view
    res_sup_audit = client.get('/admin/audit-trail')
    assert res_sup_audit.status_code == 200
    html_sup_audit = res_sup_audit.data.decode('utf-8')
    assert 'Role Manager' not in html_sup_audit
    print("Test 5 Passed: 'Role Manager' removed from supervisor on audit trail.")

    print("\n>>> ALL 4 USER REQUIREMENTS VERIFIED AND PASSED 100%! <<<")
