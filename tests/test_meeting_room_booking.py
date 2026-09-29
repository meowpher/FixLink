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

    # 5. Valid 3-hour instant ad-hoc claim for Conference Room on Ground Floor
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

    # 6. Valid 4-hour scheduled slot reservation for Meeting Room on 6th Floor
    future_date = (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
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

    # Verify 4 RoomBooking slots created
    with run_app_context:
        bookings = RoomBooking.query.filter_by(room_id=mr6_id, faculty_id=faculty_id).all()
        assert len(bookings) == 4
        adhoc_id = AdHocBooking.query.filter_by(room_id=conf0_id).first().id

    # 7. Cancel AdHocBooking via /faculty/api/adhoc/cancel/<id>
    res = client.post(f'/faculty/api/adhoc/cancel/{adhoc_id}')
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    assert 'Reservation deleted successfully' in res.get_json()['message']

    with run_app_context:
        assert AdHocBooking.query.get(adhoc_id) is None

