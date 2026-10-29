import pytest
from app import db
from app.models import Ticket, Room, Floor, Building

def test_full_ticket_lifecycle(client, student_user, admin_user, run_app_context):
    """Simulate ticket creation and Supervisor-Verified Quality Assurance Closure."""
    import io
    from app.models import AuditLog
    
    # Setup initial infrastructure
    with run_app_context:
        b = Building(name="Test Building")
        f = Floor(level=1, name="1st Floor", building=b)
        r = Room(number="TEST101", floor=f)
        db.session.add_all([b, f, r])
        db.session.commit()
        room_id = r.id

    # 1. Student creates ticket
    with client.session_transaction() as sess:
        sess['user_id'] = student_user.id
    
    response = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'electrical',
        'description': 'Light bulb broken'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    ticket_id = json_data['ticket_id']
    
    with run_app_context:
        t = db.session.get(Ticket, ticket_id)
        assert t.status == Ticket.STATUS_OPEN
        assert t.reporter_id == student_user.id
        
    # 2. Supervisor inspects work, uploads proof image, and commits verified closure
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True
        sess['tab_guard_id'] = 'secure_tab_token_123'
        
    test_img = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), 'proof.png')
    response = client.post(f'/admin/issues/{ticket_id}/verify-close', data={
        'technician_name': 'Ramesh (Electrical)',
        'resolution_notes': 'Physically inspected Room TEST101. Bulb replaced and circuit tested successfully.',
        'proof_image': test_img
    }, headers={
        'X-Requested-With': 'XMLHttpRequest',
        'X-Tab-Guard-ID': 'secure_tab_token_123'
    })
    
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data['success'] is True
    assert res_data['data']['status'] == Ticket.STATUS_RESOLVED
    assert 'proof_url' in res_data['data']

    # 3. Verify Database State and Immutable AuditLog entry
    with run_app_context:
        t = db.session.get(Ticket, ticket_id)
        assert t.status == Ticket.STATUS_RESOLVED
        assert t.verified_by_id == admin_user.id
        assert t.assigned_vendor_or_tech_name == 'Ramesh (Electrical)'
        assert 'Physically inspected' in t.resolution_notes
        assert t.proof_of_completion_url is not None
        assert t.resolved_at is not None

        audit = AuditLog.query.filter_by(target_type='Ticket', target_id=ticket_id).first()
        assert audit is not None
        assert audit.action == 'TICKET_VERIFIED_CLOSED'
        assert f"Ticket #{ticket_id} inspected, verified, and closed by Supervisor" in audit.details
        assert audit.user_id == admin_user.id


def test_daily_report_limit(client, student_user, admin_user, run_app_context):
    """Test that a user cannot submit more than 3 tickets per day (Max 3/day)."""
    with run_app_context:
        b = Building(name="Quota Building")
        f = Floor(level=2, name="2nd Floor", building=b)
        r = Room(number="VY201", floor=f)
        db.session.add_all([b, f, r])
        db.session.commit()
        room_id = r.id

    with client.session_transaction() as sess:
        sess['user_id'] = student_user.id

    # Submit 3 valid reports
    for i in range(1, 4):
        resp = client.post('/report', data={
            'room_id': room_id,
            'issue_type': 'electrical',
            'description': f'Valid distinct issue number {i} with sufficient context'
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    # 4th report on same day should be blocked with 429
    resp_fourth = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'lighting',
        'description': 'Fourth report attempt should be blocked by daily limit'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert resp_fourth.status_code == 429
    data = resp_fourth.get_json()
    assert data['success'] is False
    assert 'Daily report limit reached' in data['error']

    # Superadmin should bypass daily limit
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True

    resp_admin = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'ac',
        'description': 'Superadmin diagnostic report bypasses limit'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert resp_admin.status_code == 200
    assert resp_admin.get_json()['success'] is True


def test_spam_detection_and_auto_strike(client, student_user, run_app_context):
    """Test automated spam detection triggers rejection and records a violation strike."""
    from app.models import NoShowStrike, User

    with run_app_context:
        b = Building(name="Spam Test Building")
        f = Floor(level=3, name="3rd Floor", building=b)
        r = Room(number="VY301", floor=f)
        db.session.add_all([b, f, r])
        db.session.commit()
        room_id = r.id

    with client.session_transaction() as sess:
        sess['user_id'] = student_user.id

    # 1. Repeated character spam
    resp_spam1 = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'electrical',
        'description': 'aaaaaaaaaaaaaaaaaaaa'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert resp_spam1.status_code == 400
    data1 = resp_spam1.get_json()
    assert data1['success'] is False
    assert 'violation strike' in data1['error']

    # Verify strike record in DB
    with run_app_context:
        strikes = NoShowStrike.query.filter_by(faculty_id=student_user.id).all()
        assert len(strikes) >= 1
        assert "Spam Maintenance Report" in strikes[0].strike_reason

    # 2. Keyboard mash / gibberish spam
    resp_spam2 = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'plumbing',
        'description': 'asdfasdfasdfasdf'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert resp_spam2.status_code == 400
    data2 = resp_spam2.get_json()
    assert data2['success'] is False
    assert 'violation strike' in data2['error']

    # 3. Third spam triggers 14-day ad-hoc suspension
    resp_spam3 = client.post('/report', data={
        'room_id': room_id,
        'issue_type': 'furniture',
        'description': 'bbbbbbbbbbbbbbbbbb'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert resp_spam3.status_code == 400
    data3 = resp_spam3.get_json()
    assert 'suspended' in data3['error'].lower()

    with run_app_context:
        user = db.session.get(User, student_user.id)
        assert user.is_adhoc_suspended is True
        assert user.adhoc_suspended_until is not None


def test_supervisor_verification_security_and_validation(client, student_user, admin_user, run_app_context):
    """Verify security controls, Zero-Trust validation, and AuditLog formatting for Supervisor Verification."""
    import io
    from app.models import AuditLog

    with run_app_context:
        b = Building(name="QA Building")
        f = Floor(level=3, name="3rd Floor", building=b)
        r = Room(number="QA301", floor=f)
        db.session.add_all([b, f, r])
        db.session.commit()

        ticket = Ticket(
            room_id=r.id,
            issue_type='ac',
            description='AC not cooling in lecture hall',
            reporter_id=student_user.id,
            reporter_name=student_user.name,
            prn='12345678',
            reporter_email=student_user.email,
            status=Ticket.STATUS_OPEN
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    # 1. Non-admin user access attempt is blocked
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = student_user.id
        sess['is_admin'] = False

    test_img = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), 'proof.png')
    res_unauth = client.post(f'/admin/issues/{ticket_id}/verify-close', data={
        'technician_name': 'Vendor Tech',
        'resolution_notes': 'Fixed by non-admin',
        'proof_image': test_img
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res_unauth.status_code in [403, 302]

    # 2. Admin Zero-Trust Tab Guard token mismatch is rejected (403)
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True
        sess['tab_guard_id'] = 'legitimate_server_guard_token'

    test_img = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), 'proof.png')
    res_mismatch = client.post(f'/admin/issues/{ticket_id}/verify-close', data={
        'technician_name': 'Vendor Tech',
        'resolution_notes': 'Fixed',
        'proof_image': test_img
    }, headers={
        'X-Requested-With': 'XMLHttpRequest',
        'X-Tab-Guard-ID': 'forged_or_corrupt_tab_token'
    })
    assert res_mismatch.status_code == 403

    # 3. Missing proof image is rejected with 400
    res_no_img = client.post(f'/admin/issues/{ticket_id}/verify-close', data={
        'technician_name': 'Vendor Tech',
        'resolution_notes': 'Fixed without image'
    }, headers={
        'X-Requested-With': 'XMLHttpRequest',
        'X-Tab-Guard-ID': 'legitimate_server_guard_token'
    })
    assert res_no_img.status_code == 400

    # 4. Valid verification with correct Tab Guard and camera proof
    test_valid_img = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), 'proof_camera.png')
    res_valid = client.post(f'/admin/issues/{ticket_id}/verify-close', data={
        'technician_name': 'Voltas External Services',
        'resolution_notes': 'Compressor capacitor replaced and thermostat calibrated to 22C.',
        'proof_image': test_valid_img
    }, headers={
        'X-Requested-With': 'XMLHttpRequest',
        'X-Tab-Guard-ID': 'legitimate_server_guard_token'
    })
    assert res_valid.status_code == 200
    valid_data = res_valid.get_json()
    assert valid_data['success'] is True

    # 5. Verify immutable Audit Log entry format
    with run_app_context:
        ticket_db = db.session.get(Ticket, ticket_id)
        assert ticket_db.status == Ticket.STATUS_RESOLVED
        assert ticket_db.verified_by_id == admin_user.id
        assert ticket_db.assigned_vendor_or_tech_name == 'Voltas External Services'
        assert 'Compressor capacitor replaced' in ticket_db.resolution_notes
        assert ticket_db.proof_of_completion_url.startswith('/static/uploads/proofs/proof_')

        audit_entry = AuditLog.query.filter_by(target_type='Ticket', target_id=ticket_id).first()
        assert audit_entry is not None
        expected_msg = f"Ticket #{ticket_id} inspected, verified, and closed by Supervisor {admin_user.name} with proof attached."
        assert audit_entry.details == expected_msg
