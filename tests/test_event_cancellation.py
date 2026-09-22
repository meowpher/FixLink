import pytest
from datetime import date, time
from app import db
from app.models import User, Building, Floor, Room, EventBooking

def test_faculty_cancel_pending_and_approved_event(client, run_app_context):
    with run_app_context:
        faculty = User(name="Prof Alan", email="alan@mitwpu.edu.in", role=User.ROLE_FACULTY)
        faculty.set_password("pass123")
        admin = User(name="Admin Boss", email="admin1@mitwpu.edu.in", role=User.ROLE_ADMIN, is_admin=True)
        admin.set_password("pass123")
        b = Building(name="Vyas")
        db.session.add_all([faculty, admin, b])
        db.session.commit()

        faculty_id = faculty.id
        faculty_name = faculty.name

        fl = Floor(building_id=b.id, level=1, name="1st Floor")
        db.session.add(fl)
        db.session.commit()

        r1 = Room(floor_id=fl.id, number="101")
        db.session.add(r1)
        db.session.commit()

        # 1. Create Pending Event
        ev1 = EventBooking(
            title="AI Workshop",
            faculty_id=faculty_id,
            booking_type='rooms',
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            status='Pending'
        )
        ev1.rooms.append(r1)
        db.session.add(ev1)
        db.session.commit()
        ev1_id = ev1.id

    # Faculty cancels pending event
    with client.session_transaction() as sess:
        sess['user_id'] = faculty_id
        sess['user_name'] = faculty_name
        sess['user_role'] = User.ROLE_FACULTY

    resp = client.post(f'/faculty/events/{ev1_id}/cancel', json={'reason': 'Changed plan'})
    assert resp.status_code == 200
    assert resp.json['success'] is True

    with run_app_context:
        updated_ev1 = EventBooking.query.get(ev1_id)
        assert updated_ev1.status == 'Cancelled'
        assert 'Changed plan' in updated_ev1.rejection_reason

    # 2. Create Approved Event
    with run_app_context:
        ev2 = EventBooking(
            title="Hackathon Gala",
            faculty_id=faculty_id,
            booking_type='rooms',
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 5),
            start_time=time(14, 0),
            end_time=time(18, 0),
            status='Approved'
        )
        ev2.rooms.append(r1)
        db.session.add(ev2)
        db.session.commit()
        ev2_id = ev2.id

    # Faculty cancels approved event
    resp2 = client.post(f'/faculty/events/{ev2_id}/cancel', json={'reason': 'Guest unavailable'})
    assert resp2.status_code == 200
    assert resp2.json['success'] is True

    with run_app_context:
        updated_ev2 = EventBooking.query.get(ev2_id)
        assert updated_ev2.status == 'Cancelled'
        assert 'Guest unavailable' in updated_ev2.rejection_reason


def test_admin_reject_approved_event(client, run_app_context):
    with run_app_context:
        faculty = User(name="Prof Turing", email="turing@mitwpu.edu.in", role=User.ROLE_FACULTY)
        faculty.set_password("pass123")
        admin = User(name="Admin Super", email="admin2@mitwpu.edu.in", role=User.ROLE_ADMIN, is_admin=True)
        admin.set_password("pass123")
        db.session.add_all([faculty, admin])
        db.session.commit()

        faculty_id = faculty.id
        admin_id = admin.id
        admin_name = admin.name

        ev = EventBooking(
            title="Robotics Summit",
            faculty_id=faculty_id,
            booking_type='rooms',
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 10),
            start_time=time(9, 0),
            end_time=time(17, 0),
            status='Approved'
        )
        db.session.add(ev)
        db.session.commit()
        ev_id = ev.id

    # Admin rejects approved event
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['user_name'] = admin_name
        sess['user_role'] = User.ROLE_ADMIN
        sess['is_admin'] = True

    resp = client.post(f'/admin/events/{ev_id}/reject', json={'reason': 'Maintenance emergency scheduled on floor'})
    assert resp.status_code == 200
    assert resp.json['success'] is True

    with run_app_context:
        updated_ev = EventBooking.query.get(ev_id)
        assert updated_ev.status == 'Rejected'
        assert updated_ev.rejection_reason == 'Maintenance emergency scheduled on floor'


def test_faculty_cannot_cancel_others_event(client, run_app_context):
    with run_app_context:
        faculty1 = User(name="Prof One", email="one@mitwpu.edu.in", role=User.ROLE_FACULTY)
        faculty1.set_password("pass123")
        faculty2 = User(name="Prof Two", email="two@mitwpu.edu.in", role=User.ROLE_FACULTY)
        faculty2.set_password("pass123")
        db.session.add_all([faculty1, faculty2])
        db.session.commit()

        faculty1_id = faculty1.id
        faculty2_id = faculty2.id
        faculty2_name = faculty2.name

        ev = EventBooking(
            title="Private Seminar",
            faculty_id=faculty1_id,
            booking_type='rooms',
            start_date=date(2026, 10, 12),
            end_date=date(2026, 10, 12),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status='Approved'
        )
        db.session.add(ev)
        db.session.commit()
        ev_id = ev.id

    # Prof Two tries to cancel Prof One's event
    with client.session_transaction() as sess:
        sess['user_id'] = faculty2_id
        sess['user_name'] = faculty2_name
        sess['user_role'] = User.ROLE_FACULTY

    resp = client.post(f'/faculty/events/{ev_id}/cancel', json={'reason': 'Malicious attempt'})
    assert resp.status_code == 403
    assert resp.json['success'] is False

    with run_app_context:
        updated_ev = EventBooking.query.get(ev_id)
        assert updated_ev.status == 'Approved'
