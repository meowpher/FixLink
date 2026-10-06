import pytest
from datetime import datetime, timedelta, date, time
from app import db
from app.models import User, Building, Floor, Room, RoomBooking, AdHocBooking

def test_meeting_room_booking_full_flow(client, run_app_context):
    with run_app_context:
        # Setup users, buildings, floors, rooms
        faculty = User(name="Dr. Jane Smith", email="jane.smith@mitwpu.edu.in", role=User.ROLE_FACULTY, has_accepted_terms=True)
        faculty.set_password("secure123")
        b = Building(name="Vyas Hall")
        db.session.add_all([faculty, b])
        db.session.commit()

        faculty_id = faculty.id

        # Ground Floor (0) and 6th Floor (6)
        floor0 = Floor(building_id=b.id, level=0, name="Ground Floor")
        floor1 = Floor(building_id=b.id, level=1, name="1st Floor")
        floor6 = Floor(building_id=b.id, level=6, name="6th Floor")
        db.session.add_all([floor0, floor1, floor6])
        db.session.commit()

        # Conference room on Ground Floor
        conf0 = Room(floor_id=floor0.id, number="VY001", name="Conference Room 001", room_type=Room.ROOM_TYPE_CONFERENCE)
        # Meeting room on 6th Floor
        mr6 = Room(floor_id=floor6.id, number="MR4", name="Meeting Room 4", room_type=Room.ROOM_TYPE_MEETING)
        # Regular Classroom on 1st Floor
        class1 = Room(floor_id=floor1.id, number="VY101", name="Classroom 101", room_type=Room.ROOM_TYPE_CLASSROOM)
        db.session.add_all([conf0, mr6, class1])
        db.session.commit()

        conf0_id = conf0.id
        mr6_id = mr6.id
        class1_id = class1.id

    # Authenticate faculty
    with client.session_transaction() as sess:
        sess['user_id'] = faculty_id
        sess['user_role'] = User.ROLE_FACULTY

    # 1. GET /faculty/api/meeting-rooms should return conference and meeting rooms on Floor 0 and 6
    res = client.get('/faculty/api/meeting-rooms')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    room_numbers = [r['number'] for r in data['data']['rooms']]
    assert 'VY001' in room_numbers
    assert 'MR4' in room_numbers
    assert 'VY101' not in room_numbers

    # 2. Duration constraint check: < 1 hour should be rejected
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': conf0_id,
        'booking_type': 'instant',
        'duration_hours': 0,
        'subject': 'Quick Sync'
    })
    assert res.status_code == 400
    assert '1 hour minimum' in res.get_json()['error']

    # 3. Duration constraint check: > 4 hours should be rejected
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': conf0_id,
        'booking_type': 'instant',
        'duration_hours': 5,
        'subject': 'Marathon Workshop'
    })
    assert res.status_code == 400
    assert '4 hours maximum' in res.get_json()['error']

    # 4. Attempting to book a non-meeting room (e.g. 1st floor classroom) should be rejected
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': class1_id,
        'booking_type': 'instant',
        'duration_hours': 2,
        'subject': 'Invalid Class Booking'
    })
    assert res.status_code == 400
    assert 'only allowed for rooms on the Ground Floor' in res.get_json()['error']

    from unittest.mock import patch

    # 5. Night Instant Booking Check: Claiming at night (e.g. 11 PM IST / 17:30 UTC) should be rejected
    mock_night_utc = datetime(2026, 10, 7, 17, 30, 0)
    with patch('app.blueprints.faculty.routes.datetime') as mock_dt:
        mock_dt.utcnow.return_value = mock_night_utc
        mock_dt.combine = datetime.combine
        mock_dt.fromisoformat = datetime.fromisoformat
        res = client.post('/faculty/api/meeting-rooms/book', json={
            'room_id': conf0_id,
            'booking_type': 'instant',
            'duration_hours': 1,
            'subject': 'Night Sync Attempt'
        })
        assert res.status_code == 400
        assert 'building is closed' in res.get_json()['error']

    # 5b. Valid 3-hour instant ad-hoc claim during operational hours (e.g. 10:00 AM IST / 04:30 UTC)
    mock_day_utc = datetime(2026, 10, 7, 4, 30, 0)
    with patch('app.blueprints.faculty.routes.datetime') as mock_dt:
        mock_dt.utcnow.return_value = mock_day_utc
        mock_dt.combine = datetime.combine
        mock_dt.fromisoformat = datetime.fromisoformat
        res = client.post('/faculty/api/meeting-rooms/book', json={
            'room_id': conf0_id,
            'booking_type': 'instant',
            'duration_hours': 3,
            'subject': 'Board of Studies Conference'
        })
        assert res.status_code == 200
        assert res.get_json()['success'] is True
        assert '3 hour(s)' in res.get_json()['message']

    # Verify AdHocBooking was created in DB
    with run_app_context:
        adhoc = AdHocBooking.query.filter_by(room_id=conf0_id).first()
        assert adhoc is not None
        assert adhoc.faculty_id == faculty_id
        assert adhoc.checked_in is True

    # 6. Scheduled booking checks:
    # 6a. Booking past 6 PM slot start (e.g. 7 PM / 19:00) should be rejected
    future_date = (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': mr6_id,
        'booking_type': 'scheduled',
        'slot_start': f'{future_date}T19:00:00',
        'duration_hours': 1,
        'subject': 'Late Evening Meeting'
    })
    assert res.status_code == 400
    assert 'between 7:00 AM and 6:00 PM' in res.get_json()['error']

    # 6b. Booking starting at 6 PM (18:00) for 2 hours (ending at 8 PM) should be rejected (exceeds 7 PM closing)
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': mr6_id,
        'booking_type': 'scheduled',
        'slot_start': f'{future_date}T18:00:00',
        'duration_hours': 2,
        'subject': 'Overtime Meeting'
    })
    assert res.status_code == 400
    assert 'extend past closing hours (7:00 PM)' in res.get_json()['error']

    # 6c. Valid 4-hour scheduled slot reservation for Meeting Room on 6th Floor (10:00 AM to 2:00 PM)
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': mr6_id,
        'booking_type': 'scheduled',
        'slot_start': f'{future_date}T10:00:00',
        'duration_hours': 4,
        'subject': 'Dean Advisory Panel Meeting'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    assert '4 hour(s)' in res.get_json()['message']

    # 6d. Valid 1-hour early morning slot reservation at 7:00 AM
    res = client.post('/faculty/api/meeting-rooms/book', json={
        'room_id': mr6_id,
        'booking_type': 'scheduled',
        'slot_start': f'{future_date}T07:00:00',
        'duration_hours': 1,
        'subject': 'Early Morning Research Sync'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    # Verify RoomBooking slots created
    with run_app_context:
        bookings = RoomBooking.query.filter_by(room_id=mr6_id, faculty_id=faculty_id).all()
        assert len(bookings) == 5
        adhoc_id = AdHocBooking.query.filter_by(room_id=conf0_id).first().id

    # 7. Cancel AdHocBooking via /faculty/api/adhoc/cancel/<id>
    res = client.post(f'/faculty/api/adhoc/cancel/{adhoc_id}')
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    assert 'Reservation deleted successfully' in res.get_json()['message']

    with run_app_context:
        assert AdHocBooking.query.get(adhoc_id) is None

    # 8. Cancel RoomBooking via /faculty/api/bookings/cancel/<id>
    rb_id = bookings[0].id
    res = client.post(f'/faculty/api/bookings/cancel/{rb_id}', json={'type': 'booking'})
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    assert 'cancelled successfully' in res.get_json()['message']

    with run_app_context:
        rb = RoomBooking.query.get(rb_id)
        assert rb.status == RoomBooking.STATUS_CANCELLED


def test_classroom_booking_operating_hours_enforcement(client, run_app_context):
    """Verify that classroom bookings enforce 7 AM - 6 PM start slots and 7 PM closing limit."""
    with run_app_context:
        faculty = User(name="Dr. Alan Turing", email="alan.turing2@mitwpu.edu.in", role=User.ROLE_FACULTY, has_accepted_terms=True)
        faculty.set_password("secure123")
        b = Building(name="Vyas Hall")
        db.session.add_all([faculty, b])
        db.session.commit()

        floor = Floor(building_id=b.id, level=2, name="2nd Floor")
        db.session.add(floor)
        db.session.commit()

        room = Room(floor_id=floor.id, number="VY201", name="Vyas 201", room_type=Room.ROOM_TYPE_CLASSROOM)
        db.session.add(room)
        db.session.commit()

        faculty_id = faculty.id
        room_id = room.id

    with client.session_transaction() as sess:
        sess['user_id'] = faculty_id
        sess['user_role'] = User.ROLE_FACULTY

    future_date = (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d')

    # 1. Booking before 7 AM (e.g. 06:00) should be rejected
    res = client.post('/faculty/api/bookings/create', json={
        'room_id': room_id,
        'slot_start': f'{future_date}T06:00:00',
        'duration': 1,
        'subject': 'Pre-Dawn Class'
    })
    assert res.status_code == 400
    assert 'between 7:00 AM and 6:00 PM' in res.get_json()['error']

    # 2. Booking at 7 AM (07:00) for 1 hour should succeed
    res = client.post('/faculty/api/bookings/create', json={
        'room_id': room_id,
        'slot_start': f'{future_date}T07:00:00',
        'duration': 1,
        'subject': 'Morning 7 AM Class'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    # 3. Booking at 6 PM (18:00) for 2 hours should be rejected (ends at 8 PM, past 7 PM closing)
    res = client.post('/faculty/api/bookings/create', json={
        'room_id': room_id,
        'slot_start': f'{future_date}T18:00:00',
        'duration': 2,
        'subject': 'Extended Evening Class'
    })
    assert res.status_code == 400
    assert 'extend past closing hours (7:00 PM)' in res.get_json()['error']

    # 4. Valid 1-hour booking at 6 PM (18:00 to 19:00) should succeed
    res = client.post('/faculty/api/bookings/create', json={
        'room_id': room_id,
        'slot_start': f'{future_date}T18:00:00',
        'duration': 1,
        'subject': 'Final Slot Class'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True


def test_contiguous_room_booking_merging_on_dashboard(client, run_app_context):
    """Verify that contiguous 2-hour ad-hoc room bookings are merged into a single block with colspan=2."""
    from app.blueprints.faculty.routes import merge_contiguous_room_bookings
    
    with run_app_context:
        faculty = User(name="Dr. Alan Turing", email="alan.turing@mitwpu.edu.in", role=User.ROLE_FACULTY, has_accepted_terms=True)
        faculty.set_password("secure123")
        b = Building(name="Vyas Hall")
        db.session.add_all([faculty, b])
        db.session.commit()

        floor = Floor(building_id=b.id, level=3, name="3rd Floor")
        db.session.add(floor)
        db.session.commit()

        room = Room(floor_id=floor.id, number="VY315", name="Vyas 315", room_type=Room.ROOM_TYPE_CLASSROOM)
        db.session.add(room)
        db.session.commit()

        # Create two contiguous 1-hour bookings on Tuesday of current week
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        current_day = now.weekday()
        start_of_week = (now - timedelta(days=current_day)).date()
        tuesday_date = start_of_week + timedelta(days=1)
        slot1_start = datetime.combine(tuesday_date, time(10, 0))
        slot2_start = datetime.combine(tuesday_date, time(11, 0))

        rb1 = RoomBooking(
            room_id=room.id,
            faculty_id=faculty.id,
            date=tuesday_date,
            slot_start=slot1_start,
            subject="DSC",
            division="TY-CSE",
            course="Data Science",
            checked_in=True
        )
        rb2 = RoomBooking(
            room_id=room.id,
            faculty_id=faculty.id,
            date=tuesday_date,
            slot_start=slot2_start,
            subject="DSC",
            division="TY-CSE",
            course="Data Science",
            checked_in=True
        )
        db.session.add_all([rb1, rb2])
        db.session.commit()

        # 1. Test helper directly
        raw_list = [rb1, rb2]
        merged = merge_contiguous_room_bookings(raw_list)
        assert len(merged) == 1
        assert merged[0].duration == 2
        assert merged[0].slot_start == slot1_start
        assert merged[0].slot_end == datetime.combine(tuesday_date, time(12, 0))
        assert merged[0].subject == "DSC"
        assert len(merged[0].ids) == 2

        faculty_id = faculty.id

    # 2. Test rendered dashboard HTML contains colspan="2" and single merged cell
    with client.session_transaction() as sess:
        sess['user_id'] = faculty_id
        sess['user_role'] = User.ROLE_FACULTY

    res = client.get('/faculty/dashboard')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'colspan="2"' in html
    assert 'DSC' in html
    assert 'VY315' in html


