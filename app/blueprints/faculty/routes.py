"""
Faculty Routes Blueprint - Smart Room Scheduling
"""
from datetime import datetime, timedelta
import logging
from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from ... import db
from ...models import User, Building, Floor, Room, AdHocBooking, Timetable, RoomBooking, Notification, NoShowStrike, ScheduleSubmission, EventBooking
from ...decorators import faculty_login_required
from ...api_utils import handle_api_errors, api_response
from ...realtime import emit_room_status_change, emit_faculty_nudge

logger = logging.getLogger(__name__)

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard')
@faculty_login_required
def dashboard():
    """Faculty combined dashboard (My Schedule & Room Utilization Tracker)."""
    user_id = session.get('user_id')
    faculty = db.session.get(User, user_id)
    
    # Time context
    current_dt = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_day = current_dt.weekday() # 0 = Monday
    
    # 1. My Schedule (Include where I am primary OR collaborator)
    my_schedules = Timetable.query.filter(
        or_(Timetable.faculty_id == faculty.id, Timetable.collaborator_id == faculty.id)
    ).order_by(Timetable.day_of_week, Timetable.start_time).all()
    
    all_faculties = User.query.filter_by(role=User.ROLE_FACULTY).order_by(User.name).all()
    my_adhoc = AdHocBooking.query.filter(
        AdHocBooking.faculty_id == faculty.id,
        AdHocBooking.end_datetime >= datetime.utcnow()
    ).order_by(AdHocBooking.start_datetime).all()

    my_events = EventBooking.query.filter_by(
        faculty_id=faculty.id
    ).order_by(EventBooking.created_at.desc()).all()
    
    # 2. Floors & Rooms for Real-Time Tracker Tab
    floors = Floor.query.order_by(Floor.level).all()
    all_rooms = Room.query.all()
    
    # Group rooms by floor
    rooms_by_floor = {}
    for f in floors:
        rooms_by_floor[f.level] = [r for r in all_rooms if r.floor_id == f.id]
        
    # 3. Booking History (Paginated)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)
    history_pagination = RoomBooking.query.filter_by(
        faculty_id=faculty.id
    ).order_by(RoomBooking.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    for b in history_pagination.items:
        slot_end_dt = b.slot_end
        if slot_end_dt:
            slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
            b.is_historical = slot_end_ist < now_ist
        else:
            b.is_historical = False

    # Execute Ghost Protocol no-show cleanup before rendering dashboard
    try:
        run_ghost_protocol()
    except Exception as e:
        logger.warning(f"Ghost protocol on-load execution failed: {e}")

    # Bookings this week for the timetable grid
    start_of_week = (current_dt - timedelta(days=current_day)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    bookings_this_week = RoomBooking.query.filter(
        RoomBooking.faculty_id == faculty.id,
        RoomBooking.status == RoomBooking.STATUS_ACTIVE,
        RoomBooking.slot_start >= start_of_week,
        RoomBooking.slot_start <= end_of_week
    ).all()
    
    for b in bookings_this_week:
        slot_end_dt = b.slot_end
        if slot_end_dt:
            slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
            b.is_historical = slot_end_ist < now_ist
        else:
            b.is_historical = False

    # 3-Strike Accountability Strike Count (last 30 days)
    cutoff_30d = datetime.utcnow() - timedelta(days=30)
    recent_strikes_count = NoShowStrike.query.filter(
        NoShowStrike.faculty_id == faculty.id,
        NoShowStrike.created_at >= cutoff_30d
    ).count()

    return render_template('faculty/dashboard.html',
                           faculty=faculty,
                           floors=floors,
                           all_rooms=all_rooms,
                           all_faculties=all_faculties,
                           rooms_by_floor=rooms_by_floor,
                           my_schedules=my_schedules,
                           my_adhoc=my_adhoc,
                           my_events=my_events,
                           booking_history=history_pagination.items,
                           history_pagination=history_pagination,
                           bookings_this_week=bookings_this_week,
                           current_day=current_day,
                           recent_strikes_count=recent_strikes_count,
                           current_user_id=user_id)


@faculty_bp.route('/api/claim-room', methods=['POST'])
@faculty_login_required
@handle_api_errors
def claim_room():
    """Ad-hoc claim of an empty room by faculty with 15-minute transition dead-zone buffer."""
    data = request.get_json()
    room_id = data.get('room_id')
    duration_mins = data.get('duration_mins', 60)
    subject = data.get('subject', 'Ad-hoc Lecture').strip()
    BUFFER_MINUTES = 15
    
    if not room_id:
        return api_response(success=False, error="Room ID is required.", status=400)
        
    try:
        duration_mins = int(duration_mins)
    except:
        return api_response(success=False, error="Invalid duration.", status=400)
    
    room = Room.query.options(
        joinedload(Room.timetables),
        joinedload(Room.adhoc_bookings)
    ).filter_by(id=room_id).first_or_404()
    
    user_id = session.get('user_id')
    faculty = db.session.get(User, user_id)
    
    # Phase 7: Check 3-Strike 7-Day Lockout Suspension
    if faculty and faculty.is_adhoc_suspended:
        suspended_until_str = faculty.adhoc_suspended_until.strftime('%b %d, %Y at %I:%M %p')
        return api_response(
            success=False,
            error=f"Ad-Hoc booking privileges are temporarily suspended until {suspended_until_str} ({faculty.suspension_remaining_str}) due to 3 no-show cancellations under Ghost Protocol.",
            status=403
        )
    
    # Check if the room is vacant
    status_info = room.current_occupancy_status
    if status_info['status'] == 'occupied':
        return api_response(success=False, error=f"Room is currently occupied by {status_info.get('faculty')} for {status_info.get('subject')}.", status=400)
    
    # Calculate UTC start and end
    start_utc = datetime.utcnow()
    end_utc = start_utc + timedelta(minutes=duration_mins)
    current_dt = start_utc + timedelta(hours=5, minutes=30)
    current_day = current_dt.weekday()
    end_dt_ist = end_utc + timedelta(hours=5, minutes=30)
    
    # Check recent ad-hoc bookings transition buffer (15-min dead zone)
    recent_adhoc = AdHocBooking.query.filter(
        AdHocBooking.room_id == room.id,
        AdHocBooking.end_datetime <= start_utc,
        AdHocBooking.end_datetime + timedelta(minutes=BUFFER_MINUTES) > start_utc
    ).first()
    if recent_adhoc:
        buf_until = (recent_adhoc.end_datetime + timedelta(hours=5, minutes=30+BUFFER_MINUTES)).strftime('%I:%M %p')
        return api_response(success=False, error=f"Room is currently in a 15-minute physical transition dead-zone until {buf_until}.", status=400)
    
    for sched in room.timetables:
        if sched.day_of_week == current_day:
            sched_start = datetime.combine(current_dt.date(), sched.start_time)
            sched_end = datetime.combine(current_dt.date(), sched.end_time)
            
            # If previous lecture finished within 15 min dead zone
            if sched_end <= current_dt < sched_end + timedelta(minutes=BUFFER_MINUTES):
                buf_until = (sched_end + timedelta(minutes=BUFFER_MINUTES)).strftime('%I:%M %p')
                return api_response(success=False, error=f"Room is in a 15-minute physical transition buffer following {sched.subject} until {buf_until}.", status=400)
                
            # If the upcoming lesson starts within our selected duration + 15 min buffer
            if current_dt < sched_start < end_dt_ist + timedelta(minutes=BUFFER_MINUTES):
                return api_response(success=False, error=f"Time conflict: scheduled class for {sched.subject} starts at {sched.start_time.strftime('%I:%M %p')} (inclusive of 15-min physical transition dead-zone).", status=400)
    
    user_id = session.get('user_id')
    faculty = db.session.get(User, user_id)
    
    booking = AdHocBooking(
        room_id=room.id,
        faculty_id=user_id,
        subject=subject,
        start_datetime=start_utc,
        end_datetime=end_utc,
        checked_in=True, # Instant claim is immediately checked-in
        checked_in_at=datetime.utcnow()
    )
    
    db.session.add(booking)
    db.session.commit()
    
    # Emit pusher event
    emit_room_status_change(room, {
        'status': 'occupied',
        'type': 'adhoc',
        'subject': subject,
        'faculty': faculty.name,
        'end_time': end_dt_ist.strftime('%I:%M %p')
    })
    
    return api_response(success=True, message=f"Room VY{room.number} claimed for {duration_mins} minutes (with 15-min transition dead-zone applied).")
    

@faculty_bp.route('/api/map/status/<int:floor_id>')
@faculty_login_required
@handle_api_errors
def get_map_status(floor_id):
    """Returns room data for the selected floor in a standard map-ready format."""
    floor = Floor.query.get_or_404(floor_id)
    rooms = Room.query.filter_by(floor_id=floor_id).options(
        joinedload(Room.timetables).joinedload(Timetable.faculty),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.tickets),
        joinedload(Room.assets)
    ).all()
    
    return api_response(data={
        'floor': {
            'id': floor.id,
            'name': floor.name,
            'level': floor.level
        },
        'rooms': [room.to_map_dict() for room in rooms]
    })


@faculty_bp.route('/api/rooms/<int:room_id>/schedule', methods=['GET'])
@faculty_login_required
@handle_api_errors
def get_room_schedule(room_id):
    """Returns detailed weekly timetable and current status for a specific room."""
    room = Room.query.filter_by(id=room_id).options(
        joinedload(Room.timetables).joinedload(Timetable.faculty),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.floor)
    ).first_or_404()
    
    return api_response(data=room.to_map_dict())


@faculty_bp.route('/api/bookings/create', methods=['POST'])
@faculty_login_required
@handle_api_errors
def create_booking():
    """Validates and creates a 1-hour slot room booking."""
    data = request.get_json()
    room_id = data.get('room_id')
    slot_iso = data.get('slot_start') # Expecting ISO format 'YYYY-MM-DDTHH:MM:SS'
    subject = data.get('subject', 'Faculty Meeting')
    division = data.get('division', '')
    course = data.get('course', '')
    
    if not room_id or not slot_iso:
        return api_response(success=False, error="Room ID and slot start time are required.", status=400)
    
    user_id = session.get('user_id')
    faculty = db.session.get(User, user_id)
    
    # Phase 7: Check 3-Strike 7-Day Lockout Suspension
    if faculty and faculty.is_adhoc_suspended:
        suspended_until_str = faculty.adhoc_suspended_until.strftime('%b %d, %Y at %I:%M %p')
        return api_response(
            success=False,
            error=f"Ad-Hoc booking privileges are temporarily suspended until {suspended_until_str} ({faculty.suspension_remaining_str}) due to 3 no-show cancellations under Ghost Protocol.",
            status=403
        )
    
    try:
        # slot_iso should be interpreted as IST but stored or converted
        # The prompt says 1-hour slots like 10:00, 11:00
        slot_start = datetime.fromisoformat(slot_iso.replace('Z', ''))
        # Normalize to the beginning of the hour
        slot_start = slot_start.replace(minute=0, second=0, microsecond=0)
        duration_hours = int(data.get('duration', 1))
        if duration_hours > 2:
            return api_response(success=False, error="Maximum booking duration is 2 hours.", status=400)
        
        booking_date = slot_start.date()
        current_day = slot_start.weekday()
        user_id = session.get('user_id')
        
        # 1. Check for conflicts for ALL requested slots
        for i in range(duration_hours):
            current_slot = slot_start + timedelta(hours=i)
            slot_start_time = current_slot.time()
            slot_end_time = (current_slot + timedelta(hours=1)).time()
            
            # RoomBooking conflict
            existing_booking = RoomBooking.query.filter(
                RoomBooking.room_id == room_id,
                RoomBooking.date == booking_date,
                RoomBooking.status == RoomBooking.STATUS_ACTIVE,
                RoomBooking.slot_start < current_slot + timedelta(hours=1),
                RoomBooking.slot_start >= current_slot
            ).first()
            
            if existing_booking:
                return api_response(success=False, error=f"Room is already booked for the {current_slot.strftime('%I:%M %p')} slot.", status=400)
                
            # Timetable conflict
            existing_timetable = Timetable.query.filter(
                Timetable.room_id == room_id,
                Timetable.day_of_week == current_day,
                Timetable.start_time < slot_end_time,
                Timetable.end_time > slot_start_time
            ).first()
            
            if existing_timetable:
                return api_response(success=False, error=f"Conflict with regular class: {existing_timetable.subject}.", status=400)

        # 2. Create the bookings
        for i in range(duration_hours):
            booking = RoomBooking(
                room_id=room_id,
                faculty_id=user_id,
                date=booking_date,
                slot_start=slot_start + timedelta(hours=i),
                subject=subject,
                division=division,
                course=course
            )
            db.session.add(booking)
        
        db.session.commit()
        
        # Emit status change via pusher
        room = db.session.get(Room, room_id)
        emit_room_status_change(room, room.current_occupancy_status)
        
        return api_response(success=True, message=f"Successfully reserved for {duration_hours} hour(s).")
    except ValueError:
        return api_response(success=False, error="Invalid date/time format.", status=400)

@faculty_bp.route('/api/map/status_for_time', methods=['POST'])
@faculty_login_required
@handle_api_errors
def get_map_status_for_time():
    """Returns map occupancy based on a specific time frame."""
    data = request.get_json()
    floor_ids = data.get('floor_ids', [])
    room_type = data.get('room_type', 'all')
    start_iso = data.get('start_time')
    end_iso = data.get('end_time')
    
    if not floor_ids or not start_iso or not end_iso:
        return api_response(success=False, error="Floor IDs, start time, and end time are required.", status=400)
        
    try:
        start_dt = datetime.fromisoformat(start_iso.replace('Z', ''))
        end_dt = datetime.fromisoformat(end_iso.replace('Z', ''))
        booking_date = start_dt.date()
        current_day = start_dt.weekday()
        start_time = start_dt.time()
        end_time = end_dt.time()
        
        rooms_query = Room.query.filter(Room.floor_id.in_(floor_ids))
        if room_type != 'all':
            rooms_query = rooms_query.filter(Room.room_type == room_type)
            
        rooms = rooms_query.all()
        result_rooms = []
        
        for room in rooms:
            # Check RoomBooking
            overlapping_booking = RoomBooking.query.filter(
                RoomBooking.room_id == room.id,
                RoomBooking.date == booking_date,
                RoomBooking.status == RoomBooking.STATUS_ACTIVE,
                RoomBooking.slot_start >= start_dt,
                RoomBooking.slot_start < end_dt
            ).first()
            
            # Check Timetable
            overlapping_timetable = Timetable.query.filter(
                Timetable.room_id == room.id,
                Timetable.day_of_week == current_day,
                Timetable.start_time < end_time,
                Timetable.end_time > start_time
            ).first()
            
            is_occupied = (overlapping_booking is not None) or (overlapping_timetable is not None)
            
            status_data = 'occupied' if is_occupied else 'vacant'
            
            room_dict = room.to_map_dict()
            room_dict['occupancy'] = {'status': status_data}
            
            if is_occupied:
                subject = overlapping_booking.subject if overlapping_booking else overlapping_timetable.subject
                faculty_name = overlapping_booking.faculty.name if overlapping_booking and overlapping_booking.faculty else (overlapping_timetable.faculty.name if overlapping_timetable and overlapping_timetable.faculty else 'Unknown')
                room_dict['occupancy']['subject'] = subject
                room_dict['occupancy']['faculty'] = faculty_name
                room_dict['occupancy']['type'] = 'booking' if overlapping_booking else 'scheduled'
                room_dict['occupancy']['is_owner'] = False # For advanced search, owner status less important for viewing
            
            result_rooms.append(room_dict)
            
        return api_response(data={
            'rooms': result_rooms
        })
    except Exception as e:
        return api_response(success=False, error=str(e), status=400)


@faculty_bp.route('/api/rooms/<int:room_id>/available_slots', methods=['GET', 'POST'])
@faculty_bp.route('/api/rooms/available_slots', methods=['POST'])
@faculty_login_required
@handle_api_errors
def get_available_adhoc_slots(room_id=None):
    """
    Phase 6: The Hallway De-Escalator (Buffers & Nudges).
    When calculating available Ad-Hoc time slots, automatically injects a 15-minute 
    "dead zone" buffer after every booking to allow for physical transition.
    """
    data = request.get_json(silent=True) or {}
    target_room_id = room_id or data.get('room_id')
    date_str = data.get('date')
    
    if not target_room_id:
        return api_response(success=False, error="Room ID is required.", status=400)
        
    room = Room.query.get_or_404(target_room_id)
    BUFFER_MINUTES = 15
    
    now_local = datetime.utcnow() + timedelta(hours=5, minutes=30)
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = now_local.date()
    else:
        target_date = now_local.date()
        
    day_of_week = target_date.weekday()
    busy_intervals = []
    
    # 1. Timetable recurring classes
    for tt in room.timetables:
        if tt.day_of_week == day_of_week:
            start_dt = datetime.combine(target_date, tt.start_time)
            end_dt = datetime.combine(target_date, tt.end_time)
            buffered_end_dt = end_dt + timedelta(minutes=BUFFER_MINUTES)
            busy_intervals.append({
                'start': start_dt,
                'end': buffered_end_dt,
                'original_end': end_dt,
                'type': 'regular',
                'subject': tt.subject,
                'faculty': tt.faculty.name if tt.faculty else 'Faculty'
            })
            
    # 2. RoomBooking active slots
    bookings = RoomBooking.query.filter(
        RoomBooking.room_id == room.id,
        RoomBooking.date == target_date,
        RoomBooking.status == RoomBooking.STATUS_ACTIVE
    ).all()
    for b in bookings:
        start_dt = b.slot_start
        end_dt = b.slot_end or (start_dt + timedelta(hours=1))
        buffered_end_dt = end_dt + timedelta(minutes=BUFFER_MINUTES)
        busy_intervals.append({
            'start': start_dt,
            'end': buffered_end_dt,
            'original_end': end_dt,
            'type': 'adhoc_slot',
            'subject': b.subject or 'Reserved Slot',
            'faculty': b.faculty.name if b.faculty else 'Faculty'
        })
        
    busy_intervals.sort(key=lambda x: x['start'])
    
    # Calculate available blocks between 08:00 and 20:00
    day_start = datetime.combine(target_date, datetime.min.time().replace(hour=8, minute=0))
    day_end = datetime.combine(target_date, datetime.min.time().replace(hour=20, minute=0))
    
    available_slots = []
    current_pointer = day_start
    
    for block in busy_intervals:
        if block['start'] > current_pointer:
            slot_duration = int((block['start'] - current_pointer).total_seconds() / 60)
            if slot_duration >= 30: # 30 min minimum
                available_slots.append({
                    'start_time': current_pointer.strftime('%H:%M'),
                    'end_time': block['start'].strftime('%H:%M'),
                    'start_iso': current_pointer.isoformat(),
                    'end_iso': block['start'].isoformat(),
                    'duration_minutes': slot_duration,
                    'buffer_injected_minutes': BUFFER_MINUTES
                })
        if block['end'] > current_pointer:
            current_pointer = block['end']
            
    if day_end > current_pointer:
        slot_duration = int((day_end - current_pointer).total_seconds() / 60)
        if slot_duration >= 30:
            available_slots.append({
                'start_time': current_pointer.strftime('%H:%M'),
                'end_time': day_end.strftime('%H:%M'),
                'start_iso': current_pointer.isoformat(),
                'end_iso': day_end.isoformat(),
                'duration_minutes': slot_duration,
                'buffer_injected_minutes': BUFFER_MINUTES
            })
            
    return api_response(data={
        'room_id': room.id,
        'room_number': room.number,
        'date': target_date.isoformat(),
        'transition_dead_zone_buffer': f"{BUFFER_MINUTES} minutes",
        'available_slots': available_slots,
        'busy_blocks': [
            {
                'start': b['start'].strftime('%I:%M %p'),
                'class_end': b['original_end'].strftime('%I:%M %p'),
                'transition_buffered_end': b['end'].strftime('%I:%M %p'),
                'subject': b['subject'],
                'faculty': b['faculty']
            } for b in busy_intervals
        ]
    })


@faculty_bp.route('/api/rooms/<int:room_id>/nudge', methods=['POST'])
@faculty_bp.route('/api/rooms/nudge/<int:room_id>', methods=['POST'])
@faculty_login_required
@handle_api_errors
def nudge_faculty(room_id):
    """
    Phase 6: The Hallway De-Escalator (Nudge Feature).
    Faculty B waiting outside a room sends a polite realtime nudge to Faculty A currently occupying it.
    """
    user_id = session.get('user_id')
    sender = db.session.get(User, user_id)
    room = Room.query.options(
        joinedload(Room.timetables).joinedload(Timetable.faculty),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.adhoc_bookings).joinedload(AdHocBooking.faculty)
    ).filter_by(id=room_id).first_or_404()
    
    status_info = room.current_occupancy_status
    target_faculty_id = status_info.get('faculty_id')
    target_faculty_name = status_info.get('faculty', 'Professor')
    current_subject = status_info.get('subject', 'Current Class')
    
    if not target_faculty_id:
        return api_response(success=False, error="Room is not currently occupied by another faculty member.", status=400)
        
    if target_faculty_id == user_id:
        return api_response(success=False, error="You are listed as the current occupant of this room.", status=400)
        
    sender_name = sender.name if sender else "Next Instructor"
    
    nudge_payload = {
        'sender_faculty_id': user_id,
        'sender_faculty_name': sender_name,
        'room_id': room.id,
        'room_number': room.number,
        'subject': current_subject,
        'message': f"Prof. {sender_name} is outside Room VY{room.number} preparing for the next scheduled session. Please prepare to conclude.",
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    # 1. Trigger Pusher Real-Time Notification
    emit_faculty_nudge(target_faculty_id, nudge_payload)
    
    # 2. Persist in database notifications table
    try:
        notif = Notification(
            user_id=target_faculty_id,
            title=f"Hallway Notice: Room VY{room.number}",
            message=nudge_payload['message'],
            type=Notification.TYPE_SYSTEM,
            link="/faculty/dashboard"
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        logger.warning(f"Could not persist nudge notification: {e}")
        
    return api_response(
        success=True,
        message=f"Polite transition notice sent to Prof. {target_faculty_name}.",
        data={
            'target_faculty_id': target_faculty_id,
            'target_faculty_name': target_faculty_name,
            'room_number': room.number
        }
    )


@faculty_bp.route('/api/bookings/cancel/<int:booking_id>', methods=['POST'])
@faculty_login_required
@handle_api_errors
def cancel_booking(booking_id):
    """Cancels a faculty booking if they are the owner and not historical."""
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)

    booking = RoomBooking.query.get_or_404(booking_id)
    user_id = session.get('user_id')
    
    if booking.faculty_id != user_id:
        return api_response(success=False, error="You can only cancel your own reservations.", status=403)
        
    # Timezone-aware past/historical rejection
    slot_end_dt = booking.slot_end
    if slot_end_dt:
        slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
        if slot_end_ist < now_ist:
            return api_response(
                success=False,
                error="Action rejected: Cannot cancel or modify past/historical reservations.",
                status=400
            )

    booking.status = RoomBooking.STATUS_CANCELLED
    db.session.commit()
    
    # Update map for everyone
    if booking.room:
        emit_room_status_change(booking.room, booking.room.current_occupancy_status)
    
    return api_response(success=True, message="Reservation cancelled successfully.")


@faculty_bp.route('/api/bookings/<int:booking_id>/check_in', methods=['POST'])
@faculty_bp.route('/api/bookings/check-in/<int:booking_id>', methods=['POST'])
@faculty_bp.route('/api/adhoc/<int:booking_id>/check_in', methods=['POST'])
@faculty_login_required
@handle_api_errors
def check_in_booking(booking_id):
    """
    Check-In endpoint for Ad-Hoc and Slot bookings (Phase 5 Ghost Protocol).
    Secures the room reservation and marks the session as active and present.
    """
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)

    user_id = session.get('user_id')
    
    # Check RoomBooking first
    booking = RoomBooking.query.get(booking_id)
    if not booking:
        booking = AdHocBooking.query.get(booking_id)
        
    if not booking:
        return api_response(success=False, error="Reservation record not found.", status=404)
        
    if booking.faculty_id != user_id:
        return api_response(success=False, error="You can only check in to your own reservations.", status=403)
        
    if hasattr(booking, 'status') and booking.status == RoomBooking.STATUS_CANCELLED:
        return api_response(success=False, error="This booking has already been cancelled or expired under Ghost Protocol.", status=400)
        
    # Timezone-aware check: Cannot check into past/historical sessions
    slot_end_dt = getattr(booking, 'slot_end', None) or getattr(booking, 'end_datetime', None)
    if slot_end_dt:
        slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
        if slot_end_ist < now_ist:
            return api_response(
                success=False,
                error="Action rejected: Cannot check into past/historical reservations.",
                status=400
            )

    booking.checked_in = True
    booking.checked_in_at = datetime.utcnow()
    db.session.commit()
    
    # Broadcast updated room status if needed
    if hasattr(booking, 'room') and booking.room:
        emit_room_status_change(booking.room, booking.room.current_occupancy_status)
        
    return api_response(
        success=True, 
        message="Checked in successfully! Your room reservation is secured.",
        data={
            'booking_id': booking.id,
            'checked_in': True,
            'checked_in_at': booking.checked_in_at.isoformat() + 'Z'
        }
    )


@faculty_bp.route('/api/slots/<int:slot_id>', methods=['GET'])
@faculty_bp.route('/api/bookings/<int:slot_id>', methods=['GET'])
@faculty_bp.route('/api/slot-detail/<int:slot_id>', methods=['GET'])
@faculty_login_required
@handle_api_errors
def get_slot_detail_api(slot_id):
    """
    Returns enriched, timezone-aware SlotDetail payload for modal / card inspection.
    Flags is_historical strictly based on IST datetime comparison.
    """
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)

    booking = RoomBooking.query.get(slot_id)
    if not booking:
        booking = AdHocBooking.query.get(slot_id)
        
    if not booking:
        return api_response(success=False, error="Slot reservation not found.", status=404)

    slot_end_dt = getattr(booking, 'slot_end', None) or getattr(booking, 'end_datetime', None)
    if slot_end_dt:
        slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
        is_historical = slot_end_ist < now_ist
    else:
        is_historical = False

    data = {
        'id': booking.id,
        'subject': getattr(booking, 'subject', 'Class Session'),
        'division': getattr(booking, 'division', ''),
        'course': getattr(booking, 'course', ''),
        'room_id': booking.room.id if booking.room else None,
        'room_number': booking.room.number if booking.room else 'Unknown',
        'floor_level': booking.room.floor.level if (booking.room and booking.room.floor) else None,
        'floor_name': booking.room.floor.name if (booking.room and booking.room.floor) else '',
        'faculty_id': booking.faculty_id,
        'faculty_name': booking.faculty.name if booking.faculty else 'Faculty Member',
        'faculty_email': booking.faculty.email if booking.faculty else '',
        'status': getattr(booking, 'status', 'active'),
        'checked_in': getattr(booking, 'checked_in', False),
        'checked_in_at': booking.checked_in_at.isoformat() + 'Z' if getattr(booking, 'checked_in_at', None) else None,
        'is_historical': is_historical,
        'can_cancel': (not is_historical) and getattr(booking, 'status', 'active') != RoomBooking.STATUS_CANCELLED and booking.faculty_id == session.get('user_id'),
        'can_check_in': (not is_historical) and (not getattr(booking, 'checked_in', False)) and getattr(booking, 'status', 'active') != RoomBooking.STATUS_CANCELLED and booking.faculty_id == session.get('user_id')
    }
    return api_response(success=True, data=data)


@faculty_bp.route('/api/bookings/history', methods=['GET'])
@faculty_login_required
@handle_api_errors
def get_booking_history_api():
    """
    Returns server-side paginated booking history (limit=20) with timezone-aware is_historical flags.
    """
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)

    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pagination = RoomBooking.query.filter_by(
        faculty_id=user_id
    ).order_by(RoomBooking.slot_start.desc()).paginate(page=page, per_page=per_page, error_out=False)

    data = []
    for b in pagination.items:
        d = b.to_dict()
        slot_end_dt = b.slot_end
        if slot_end_dt:
            slot_end_ist = IST.localize(slot_end_dt) if slot_end_dt.tzinfo is None else slot_end_dt.astimezone(IST)
            d['is_historical'] = slot_end_ist < now_ist
        else:
            d['is_historical'] = False
        data.append(d)

    return api_response(
        success=True,
        data=data,
        pagination={
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num,
            'next_page': pagination.next_num
        }
    )


def record_no_show_strike(faculty_id, booking_id=None, room_id=None):
    """
    Phase 7: The 3-Strike Accountability Engine.
    Records a Ghost Protocol auto-cancel strike for a user.
    If 3 strikes occur in a rolling 30-day window, suspends Ad-Hoc booking privileges for 7 days.
    """
    if not faculty_id:
        return 0
    try:
        strike = NoShowStrike(
            faculty_id=faculty_id,
            booking_id=booking_id,
            room_id=room_id,
            strike_reason="Ghost Protocol: 10-Minute Check-In Expired",
            created_at=datetime.utcnow()
        )
        db.session.add(strike)
        db.session.commit()
        
        # Check rolling 30-day window
        cutoff_30d = datetime.utcnow() - timedelta(days=30)
        strike_count = NoShowStrike.query.filter(
            NoShowStrike.faculty_id == faculty_id,
            NoShowStrike.created_at >= cutoff_30d
        ).count()
        
        if strike_count >= 3:
            user = db.session.get(User, faculty_id)
            if user:
                user.adhoc_suspended_until = datetime.utcnow() + timedelta(days=7)
                user.adhoc_suspension_reason = f"3 Ghost Protocol no-shows in 30-day rolling window ({strike_count} strikes recorded)"
                db.session.commit()
                logger.warning(f"User {faculty_id} ({user.name}) suspended from Ad-Hoc booking until {user.adhoc_suspended_until} (3 strikes).")
                
                try:
                    notif = Notification(
                        user_id=faculty_id,
                        title="Ad-Hoc Booking Privileges Suspended (3 Strikes)",
                        message=f"You have accumulated {strike_count} no-shows under Ghost Protocol in the last 30 days. Ad-Hoc booking privileges are temporarily suspended for 7 days until {(datetime.utcnow() + timedelta(days=7)).strftime('%b %d, %Y %I:%M %p')}.",
                        type=Notification.TYPE_SYSTEM,
                        link="/faculty/dashboard"
                    )
                    db.session.add(notif)
                    db.session.commit()
                except Exception as ne:
                    logger.warning(f"Could not persist strike notification: {ne}")

                # Permanent suspension audit log
                try:
                    from ...models import SuspensionLog
                    log_entry = SuspensionLog(
                        faculty_id=faculty_id,
                        event_type=SuspensionLog.EVENT_SUSPENDED,
                        reason=user.adhoc_suspension_reason,
                        suspended_until=user.adhoc_suspended_until,
                        strike_count=strike_count
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                except Exception as le:
                    logger.warning(f"Could not persist SuspensionLog: {le}")
        return strike_count
    except Exception as e:
        logger.error(f"Failed to record NoShowStrike for faculty {faculty_id}: {e}")
        return 0


def run_ghost_protocol(app=None):
    """
    Phase 5 & 7: The Ghost Protocol (No-Show Prevention Engine) & 3-Strike Accountability Engine.
    Monitors Ad-Hoc start times.
    If faculty does not check in by 10 minutes past start time,
    the backend auto-cancels/deletes the booking, frees the room on the live map,
    and logs a No-Show strike toward the 3-strike 7-day suspension lockout.
    """
    now_utc = datetime.utcnow()
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    cancelled_count = 0
    cutoff = timedelta(minutes=10)
    
    # 1. Process active RoomBookings with unchecked status where slot started >10 min ago
    active_room_bookings = RoomBooking.query.filter(
        RoomBooking.status == RoomBooking.STATUS_ACTIVE,
        RoomBooking.checked_in == False
    ).all()
    
    for rb in active_room_bookings:
        # Check against local IST or UTC start
        is_overdue = False
        if rb.date < now_ist.date():
            is_overdue = True
        elif rb.date == now_ist.date():
            if rb.slot_start + cutoff <= now_ist or rb.slot_start + cutoff <= now_utc:
                is_overdue = True
        elif rb.slot_start + cutoff <= now_utc:
            is_overdue = True
            
        if is_overdue:
            faculty_id = rb.faculty_id
            booking_id = rb.id
            room_id = rb.room_id
            room = rb.room
            rb.status = RoomBooking.STATUS_CANCELLED
            db.session.commit()
            cancelled_count += 1
            
            # Phase 7: Record Strike and trigger 7-day suspension if >= 3 in 30 days
            record_no_show_strike(faculty_id=faculty_id, booking_id=booking_id, room_id=room_id)
            
            if room:
                emit_room_status_change(room, {'status': 'vacant'})
                
    # 2. Process active AdHocBookings
    active_adhoc_bookings = AdHocBooking.query.filter(
        AdHocBooking.checked_in == False,
        AdHocBooking.start_datetime + cutoff <= now_utc,
        AdHocBooking.end_datetime >= now_utc
    ).all()
    
    for ah in active_adhoc_bookings:
        faculty_id = ah.faculty_id
        booking_id = ah.id
        room_id = ah.room_id
        room = ah.room
        db.session.delete(ah)
        db.session.commit()
        cancelled_count += 1
        
        # Phase 7: Record Strike and trigger 7-day suspension if >= 3 in 30 days
        record_no_show_strike(faculty_id=faculty_id, booking_id=booking_id, room_id=room_id)
        
        if room:
            emit_room_status_change(room, {'status': 'vacant'})
            
    return cancelled_count


@faculty_bp.route('/api/cron/ghost_protocol', methods=['GET', 'POST'])
@faculty_bp.route('/api/cron/ghost-protocol', methods=['GET', 'POST'])
@handle_api_errors
def trigger_ghost_protocol():
    """Endpoint for cron services or heartbeats to run Ghost Protocol."""
    count = run_ghost_protocol()
    return api_response(
        success=True,
        message=f"Ghost Protocol execution complete. {count} no-show reservation(s) auto-released.",
        data={'released_count': count}
    )


@faculty_bp.route('/api/timetable/cancel/<int:timetable_id>', methods=['POST'])
@faculty_login_required
@handle_api_errors
def cancel_timetable_session(timetable_id):
    """Marks a recurring timetable session as 'Cancelled' for the CURRENT slot only."""
    # Since Timetable is recurring, we don't 'delete' it. 
    # Instead, we create a RoomBooking with status 'cancelled' or similar to override it?
    # Actually, the user says "cancelling their reservation". 
    # If it's a regular class, maybe they are just marking it as 'not happening today'.
    
    tt = Timetable.query.get_or_404(timetable_id)
    user_id = session.get('user_id')
    
    if tt.faculty_id != user_id:
        return api_response(success=False, error="You can only cancel your own classes.", status=403)
    
    # Create a 'cancelled' RoomBooking for today to override the timetable entry
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_hour_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    # Check if an override already exists
    override = RoomBooking(
        room_id=tt.room_id,
        faculty_id=user_id,
        date=now_ist.date(),
        slot_start=current_hour_utc,
        status=RoomBooking.STATUS_CANCELLED,
        subject=f"CANCELLED: {tt.subject}"
    )
    db.session.add(override)
    db.session.commit()
    
    emit_room_status_change(tt.room, tt.room.current_occupancy_status)
    return api_response(success=True, message="Class marked as cancelled for this hour.")



@faculty_bp.route('/api/faculty/timetable/<int:entry_id>', methods=['DELETE'])
@faculty_login_required
@handle_api_errors
def delete_timetable_entry(entry_id):
    """Deletes a specific timetable entry."""
    entry = Timetable.query.get_or_404(entry_id)
    user_id = session.get('user_id')
    
    if entry.faculty_id != user_id:
        return api_response(success=False, error="You can only delete classes where you are the primary faculty.", status=403)
        
    db.session.delete(entry)
    db.session.commit()
    
    return api_response(success=True, message="Class removed from your timetable.")


# =========================================================================
# CSV TIMETABLE IMPORT & PREVIEW LOGIC
# =========================================================================
import csv
import io
import re

DAY_MAP = {
    'mon': 0, 'monday': 0, '0': 0,
    'tue': 1, 'tuesday': 1, '1': 1,
    'wed': 2, 'wednesday': 2, '2': 2,
    'thu': 3, 'thursday': 3, '3': 3,
    'fri': 4, 'friday': 4, '4': 4,
    'sat': 5, 'saturday': 5, '5': 5,
    'sun': 6, 'sunday': 6, '6': 6
}

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def parse_time_slot(time_str):
    """
    Parses time strings like '10:00 - 11:00', '10:00-11:00', '10:00 AM - 11:00 AM', '10:00', '10'.
    Returns (start_time_obj, end_time_obj, duration_hours) or None.
    """
    if not time_str:
        return None
    s = str(time_str).strip().lower()
    
    parts = re.split(r'[-–—]|(?:\bto\b)', s)
    start_str = parts[0].strip()
    end_str = parts[1].strip() if len(parts) > 1 else None
    
    def parse_single_time(t_str):
        m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', t_str)
        if not m:
            return None
        hr = int(m.group(1))
        mn = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        
        # Academic standard daytime normalization: 8..11 are AM, 12 is noon, 1..7 are PM
        if 8 <= hr <= 11:
            # 8, 9, 10, 11 AM
            pass
        elif hr == 12:
            pass
        elif 1 <= hr <= 7:
            hr += 12
        elif hr >= 20:  # Erroneous 8 PM..11 PM mistakenly parsed from morning headers
            hr -= 12
            
        if 0 <= hr <= 23 and 0 <= mn <= 59:
            return datetime.strptime(f"{hr:02d}:{mn:02d}", "%H:%M").time()
        return None

    st_time = parse_single_time(start_str)
    if not st_time:
        return None
        
    if end_str:
        end_time = parse_single_time(end_str)
    else:
        end_time = (datetime.combine(datetime.today(), st_time) + timedelta(hours=1)).time()
        
    if not end_time:
        end_time = (datetime.combine(datetime.today(), st_time) + timedelta(hours=1)).time()
        
    dt_st = datetime.combine(datetime.today(), st_time)
    dt_end = datetime.combine(datetime.today(), end_time)
    if dt_end <= dt_st:
        dt_end = dt_st + timedelta(hours=1)
    duration = int(round((dt_end - dt_st).total_seconds() / 3600))
    if duration <= 0 or duration > 6:
        duration = 1
        end_time = (dt_st + timedelta(hours=1)).time()
    return st_time, end_time, duration


def parse_timetable_subject_metadata(raw_string):
    """
    Parses a raw timetable cell string (e.g., 'SYBCA DIV-A DS', 'SYMCA DIV E (11.00-12.00)', 'SYBSC-Div B C++')
    and extracts structured metadata:
    Returns dict:
    {
        'course': str or None,     # e.g., 'SYBCA', 'SYMCA', 'SYBSC', 'BSc CS Honours', 'BCA Honours'
        'division': str or None,   # e.g., 'Div A', 'Div B', 'Div E'
        'subject': str             # e.g., 'Data Structures (DS)', 'Python Programming', 'General Lecture'
    }
    """
    if not raw_string:
        return {'course': None, 'division': None, 'subject': 'General Lecture'}
    
    text = str(raw_string).strip()
    
    # 1. Strip redundant embedded time slot patterns like (11.00-12.00), 9.00-12.00, 10:00-11:00
    time_slot_regex = r'\(?\s*\d{1,2}(?:[\.:]\d{2})?\s*(?:am|pm)?\s*[-–—to\s]+\s*\d{1,2}(?:[\.:]\d{2})?\s*(?:am|pm)?\s*\)?'
    text = re.sub(time_slot_regex, ' ', text, flags=re.IGNORECASE)
    
    # 2. Extract Division (e.g., DIV-A, DIV A, Div B, Batch 1, -Div B, -B)
    division = None
    div_match = re.search(r'\b(?:div(?:ision)?|batch|sec(?:tion)?)[.\s\-_]*([A-Z0-9]+)\b', text, re.IGNORECASE)
    if div_match:
        div_val = div_match.group(1).upper()
        division = f"Batch {div_val}" if div_val.isdigit() else f"Div {div_val}"
        text = text[:div_match.start()] + ' ' + text[div_match.end():]
    else:
        div_alt = re.search(r'[\-_]([A-E])\b', text)
        if div_alt:
            div_val = div_alt.group(1).upper()
            division = f"Div {div_val}"
            text = text[:div_alt.start()] + ' ' + text[div_alt.end():]

    # 3. Extract Course & Year
    # Structured degree program patterns:
    course = None
    course_regex = re.compile(
        r'\b('
        r'(?:FY|SY|TY|4TH\s*YEAR|FINAL\s*YEAR)?[\s\-_]*(?:BSC|B\.SC)(?:[\s\-_]*(?:CS|IT|DS|AI|DATA\s*SCIENCE))?(?:[\s\-_]*(?:HONORS|HONOURS|HONS))?'
        r'|'
        r'(?:FY|SY|TY|4TH\s*YEAR|FINAL\s*YEAR)?[\s\-_]*(?:MSC|M\.SC)(?:[\s\-_]*(?:CS|IT|DS|AI|DATA\s*SCIENCE))?'
        r'|'
        r'(?:FY|SY|TY|4TH\s*YEAR|FINAL\s*YEAR)?[\s\-_]*BCA(?:[\s\-_]*(?:HONORS|HONOURS|HONS))?'
        r'|'
        r'(?:FY|SY|TY|4TH\s*YEAR|FINAL\s*YEAR)?[\s\-_]*MCA'
        r'|'
        r'(?:FY|SY|TY|4TH\s*YEAR|FINAL\s*YEAR)?[\s\-_]*BTECH(?:[\s\-_]*(?:CS|IT|DS|AI|DATA\s*SCIENCE))?'
        r')\b',
        re.IGNORECASE
    )
    
    course_match = course_regex.search(text)
    if course_match and course_match.group(1).strip():
        raw_course = course_match.group(1).strip()
        clean_course = re.sub(r'\s+', ' ', raw_course).upper()
        clean_course = re.sub(r'\bB\.SC\b', 'BSC', clean_course)
        clean_course = re.sub(r'\bM\.SC\b', 'MSC', clean_course)
        clean_course = re.sub(r'\bHONOURS\b|\bHONORS\b', 'HONS', clean_course)
        clean_course = re.sub(r'[\-_]', ' ', clean_course)
        clean_course = re.sub(r'\s+', ' ', clean_course).strip()
        
        if clean_course in ['BSC CS HONS', 'BSC CS HONORS']:
            course = 'BSc CS Honours'
        elif clean_course in ['BCA HONS', 'BCA HONORS']:
            course = 'BCA Honours'
        elif clean_course == 'BSC CS':
            course = 'BSc Computer Science'
        elif clean_course == 'BSC IT':
            course = 'BSc Information Technology'
        elif clean_course.startswith('SYBCA'):
            course = 'SYBCA'
        elif clean_course.startswith('SYMCA'):
            course = 'SYMCA'
        elif clean_course.startswith('SYBSC'):
            course = 'SYBSC'
        elif clean_course.startswith('FYMCA'):
            course = 'FYMCA'
        elif clean_course.startswith('FYBCA'):
            course = 'FYBCA'
        elif clean_course.startswith('TYBCA'):
            course = 'TYBCA'
        elif clean_course.startswith('TYBSC'):
            course = 'TYBSC'
        else:
            course = clean_course
            
        text = text[:course_match.start()] + ' ' + text[course_match.end():]
    else:
        standalone_match = re.search(r'^(BCA|MCA|BSC|MSC)\b', text, re.IGNORECASE)
        if standalone_match:
            course = standalone_match.group(1).upper()
            text = text[standalone_match.end():]

    # 4. Clean up remaining subject string
    clean_subj = re.sub(r'^[\s\-_:;,./\(\)\[\]]+|[\s\-_:;,./\(\)\[\]]+$', '', text).strip()
    clean_subj = re.sub(r'\s*[\-_:/]\s*', ' ', clean_subj)
    clean_subj = re.sub(r'\s+', ' ', clean_subj).strip()
    
    SUBJECT_MAP = {
        'DS': 'Data Structures (DS)',
        'DATA STRUCTURES': 'Data Structures',
        'PYTHON': 'Python Programming',
        'PYTHON PROGRAMMING': 'Python Programming',
        'C++': 'C++ Programming',
        'CPP': 'C++ Programming',
        'JAVA': 'Java Programming',
        'DBMS': 'Database Management Systems (DBMS)',
        'OS': 'Operating Systems (OS)',
        'CN': 'Computer Networks (CN)',
        'SE': 'Software Engineering (SE)',
        'AI': 'Artificial Intelligence (AI)',
        'ML': 'Machine Learning (ML)',
        'AI & ML': 'Artificial Intelligence & Machine Learning',
        'AI/ML': 'Artificial Intelligence & Machine Learning',
        'DAA': 'Design and Analysis of Algorithms (DAA)',
        'WT': 'Web Technologies (WT)',
        'WEB DEV': 'Web Development',
        'WEB DEVELOPMENT': 'Web Development',
        'MATHS': 'Mathematics',
        'MATH': 'Mathematics',
        'STATS': 'Statistics',
        'STATISTICS': 'Statistics',
        'IOT': 'Internet of Things (IoT)',
        'CLOUD': 'Cloud Computing',
        'CLOUD COMPUTING': 'Cloud Computing',
    }
    
    clean_upper = clean_subj.upper()
    if clean_upper in SUBJECT_MAP:
        subject = SUBJECT_MAP[clean_upper]
    elif len(clean_subj) >= 2:
        if clean_subj.isupper() and len(clean_subj) > 3:
            subject = clean_subj.title()
        else:
            subject = clean_subj
    else:
        if course:
            subject = 'General Lecture'
        else:
            subject = raw_string.strip() if raw_string.strip() else 'General Lecture'
            
    return {
        'course': course,
        'division': division,
        'subject': subject
    }


def resolve_room(room_raw, room_dict):
    """
    Resolves raw room string against room_dict containing Room models.
    """
    if not room_raw:
        return None
    raw_clean = re.sub(r'[^A-Z0-9]', '', str(room_raw).strip().upper())
    if not raw_clean:
        return None
    
    if raw_clean in room_dict:
        return room_dict[raw_clean]
        
    if not raw_clean.startswith('VY'):
        if f"VY{raw_clean}" in room_dict:
            return room_dict[f"VY{raw_clean}"]
            
    m = re.search(r'(\d{3})', raw_clean)
    if m:
        digits = m.group(1)
        if f"VY{digits}" in room_dict:
            return room_dict[f"VY{digits}"]
            
    return None


def parse_timetable_csv(file_bytes):
    """
    Parses a CSV file stream supporting Matrix/Grid layout and Row-list layout.
    Returns (parsed_entries, error_messages).
    """
    text = None
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if not text:
        return [], ["Unable to decode file content. Please upload a valid CSV file."]

    stream = io.StringIO(text)
    try:
        reader = list(csv.reader(stream))
    except Exception as e:
        return [], [f"CSV parsing error: {str(e)}"]

    if not reader:
        return [], ["CSV file is empty."]

    # Auto-detect Header row (search first 15 rows)
    header_idx = -1
    room_col_idx = -1
    time_col_idx = -1
    day_cols = {}
    is_matrix = False
    day_single_col_idx = -1
    subject_col_idx = -1

    for idx, row in enumerate(reader[:15]):
        row_clean = [str(cell).strip().lower() for cell in row]
        
        # Search for room column
        r_idx = -1
        for c_idx, cell in enumerate(row_clean):
            if any(k in cell for k in ['room', 'room no', 'room_no', 'classroom', 'lab', 'hall']):
                r_idx = c_idx
                break
                
        # Search for time column
        t_idx = -1
        for c_idx, cell in enumerate(row_clean):
            if any(k in cell for k in ['time', 'slot', 'timing', 'duration', 'hour']):
                t_idx = c_idx
                break
                
        # Search for day columns
        d_cols = {}
        for c_idx, cell in enumerate(row_clean):
            for day_k, day_v in DAY_MAP.items():
                if len(day_k) >= 3 and day_k in cell:
                    d_cols[c_idx] = day_v
                    break
                    
        if r_idx != -1 and (t_idx != -1 or d_cols):
            header_idx = idx
            room_col_idx = r_idx
            time_col_idx = t_idx
            
            has_single_day_col = any(k == 'day' or k == 'weekday' for cell in row_clean for k in cell.split())
            if d_cols and not has_single_day_col:
                is_matrix = True
                day_cols = d_cols
            elif len(d_cols) >= 2:
                is_matrix = True
                day_cols = d_cols
            else:
                is_matrix = False
                for c_idx, cell in enumerate(row_clean):
                    if any(k in cell for k in ['day', 'weekday']):
                        day_single_col_idx = c_idx
                    if any(k in cell for k in ['subject', 'course', 'class', 'title', 'paper']):
                        subject_col_idx = c_idx
            break

    if header_idx == -1:
        return [], ["Header row not detected. Please ensure CSV contains headers like 'Room No', 'Time', 'Mon', 'Tue'..."]

    all_rooms = Room.query.all()
    room_dict = {}
    for r in all_rooms:
        clean_num = re.sub(r'[^A-Z0-9]', '', r.number.upper())
        room_dict[clean_num] = r
        if r.name:
            clean_name = re.sub(r'[^A-Z0-9]', '', r.name.upper())
            room_dict[clean_name] = r

    parsed_entries = []
    errors = []
    
    current_room_raw = None
    current_time_raw = None

    for row_num, row in enumerate(reader[header_idx + 1:], start=header_idx + 2):
        if not any(cell.strip() for cell in row):
            continue
            
        r_cell = row[room_col_idx].strip() if room_col_idx < len(row) else ''
        t_cell = row[time_col_idx].strip() if time_col_idx != -1 and time_col_idx < len(row) else ''
        
        if r_cell:
            current_room_raw = r_cell
        if t_cell:
            current_time_raw = t_cell
            
        if not current_room_raw:
            continue
            
        room_obj = resolve_room(current_room_raw, room_dict)
        if not room_obj:
            errors.append(f"Row {row_num}: Room '{current_room_raw}' not found in Vyas Building.")
            continue

        if is_matrix:
            if not current_time_raw:
                errors.append(f"Row {row_num}: Missing time slot for Room {room_obj.number}.")
                continue
                
            time_parsed = parse_time_slot(current_time_raw)
            if not time_parsed:
                errors.append(f"Row {row_num}: Could not parse time '{current_time_raw}'.")
                continue
            start_t, end_t, duration = time_parsed

            for c_idx, day_num in day_cols.items():
                if c_idx < len(row):
                    raw_subj = row[c_idx].strip()
                    if raw_subj and raw_subj.upper() not in ['-', 'N/A', 'NA', 'FREE', 'OFF', 'N/L', 'BREAK', 'LUNCH']:
                        meta = parse_timetable_subject_metadata(raw_subj)
                        parsed_entries.append({
                            'room_id': room_obj.id,
                            'room_number': room_obj.number,
                            'day_of_week': day_num,
                            'day_name': DAY_NAMES[day_num],
                            'start_time': start_t.strftime('%H:%M'),
                            'end_time': end_t.strftime('%H:%M'),
                            'duration': duration,
                            'subject': meta['subject'],
                            'course': meta['course'],
                            'division': meta['division'],
                            'faculty_id': None
                        })
        else:
            day_val = row[day_single_col_idx].strip().lower() if day_single_col_idx != -1 and day_single_col_idx < len(row) else ''
            raw_subj = row[subject_col_idx].strip() if subject_col_idx != -1 and subject_col_idx < len(row) else ''
            
            if not raw_subj or raw_subj.upper() in ['-', 'N/A', 'NA', 'FREE', 'OFF', 'N/L', 'BREAK', 'LUNCH']:
                continue
                
            day_num = None
            for k, v in DAY_MAP.items():
                if k in day_val:
                    day_num = v
                    break
            if day_num is None:
                errors.append(f"Row {row_num}: Unknown day '{day_val}'.")
                continue

            time_parsed = parse_time_slot(current_time_raw)
            if not time_parsed:
                errors.append(f"Row {row_num}: Could not parse time '{current_time_raw}'.")
                continue
            start_t, end_t, duration = time_parsed

            meta = parse_timetable_subject_metadata(raw_subj)
            parsed_entries.append({
                'room_id': room_obj.id,
                'room_number': room_obj.number,
                'day_of_week': day_num,
                'day_name': DAY_NAMES[day_num],
                'start_time': start_t.strftime('%H:%M'),
                'end_time': end_t.strftime('%H:%M'),
                'duration': duration,
                'subject': meta['subject'],
                'course': meta['course'],
                'division': meta['division'],
                'faculty_id': None
            })

    return parsed_entries, errors


@faculty_bp.route('/api/timetable/preview-csv', methods=['POST'])
@faculty_login_required
@handle_api_errors
def preview_timetable_csv():
    """Validates and dry-runs a CSV timetable upload without database commit. Admin access required."""
    if not session.get('is_admin'):
        return api_response(success=False, error="Mass CSV import is restricted to Admin accounts.", status=403)

    if 'csvFile' not in request.files and 'file' not in request.files:
        return api_response(success=False, error="No CSV file uploaded.", status=400)

    file_obj = request.files.get('csvFile') or request.files.get('file')
    if not file_obj or file_obj.filename == '':
        return api_response(success=False, error="Empty file uploaded.", status=400)

    file_bytes = file_obj.read()
    parsed_entries, errors = parse_timetable_csv(file_bytes)

    return api_response(
        success=True,
        data={
            'records_parsed': len(parsed_entries),
            'error_count': len(errors),
            'errors': errors,
            'parsed_entries': parsed_entries
        }
    )


@faculty_bp.route('/api/timetable/import-csv', methods=['POST'])
@faculty_login_required
@handle_api_errors
def import_timetable_csv():
    """Commits dry-run parsed CSV timetable entries into the database. Admin access required."""
    if not session.get('is_admin'):
        return api_response(success=False, error="Mass CSV import is restricted to Admin accounts.", status=403)

    data = request.get_json()
    entries = data.get('entries', []) if data else []
    
    if not entries or not isinstance(entries, list):
        return api_response(success=False, error="No timetable entries provided to commit.", status=400)

    success_count = 0

    for entry in entries:
        room_id = entry.get('room_id')
        day = entry.get('day_of_week')
        start_time_str = entry.get('start_time')
        subject = entry.get('subject')
        course = entry.get('course')
        division = entry.get('division')
        duration = int(entry.get('duration', 1))
        fac_id = entry.get('faculty_id') or None  # Explicit None when unassigned; no admin fallback

        if not all([room_id, day is not None, start_time_str, subject]):
            continue

        try:
            start_dt = datetime.strptime(start_time_str, '%H:%M')
            start_time = start_dt.time()
            end_time = (start_dt + timedelta(hours=duration)).time()
        except Exception:
            continue

        # For mass admin import, match existing timetable by room_id, day_of_week, start_time
        existing = Timetable.query.filter_by(
            room_id=room_id,
            day_of_week=day,
            start_time=start_time
        ).first()

        if existing:
            existing.subject = subject
            existing.course = course
            existing.division = division
            existing.end_time = end_time
            existing.faculty_id = fac_id
        else:
            new_entry = Timetable(
                room_id=room_id,
                faculty_id=fac_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                subject=subject,
                course=course,
                division=division
            )
            db.session.add(new_entry)

        success_count += 1

    db.session.commit()
    return api_response(success=True, message=f"Successfully imported {success_count} timetable records into building schedule.")


@faculty_bp.route('/events/book', methods=['GET', 'POST'])
@faculty_login_required
def book_event():
    from ...models import Floor, Room, EventBooking, Notification
    from datetime import datetime
    
    if request.method == 'GET':
        floors = Floor.query.order_by(Floor.level).all()
        for f in floors:
            f.rooms.sort(key=lambda r: r.number)
        return render_template('faculty/book_event.html', floors=floors)
        
    try:
        data = request.json
        title = data.get('title')
        desc = data.get('description', '')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        b_type = data.get('booking_type', 'rooms')
        targets = data.get('targets', [])
        
        if not title or not start_date_str or not end_date_str or not start_time_str or not end_time_str or not targets:
            return api_response(success=False, error="Missing required fields", status=400)
            
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        if end_date < start_date:
            return api_response(success=False, error="End date cannot be before start date.", status=400)
        if start_date == end_date and end_time <= start_time:
            return api_response(success=False, error="End time must be after start time.", status=400)
            
        from sqlalchemy import and_, or_
        from ... import db
        
        overlap_events = EventBooking.query.filter(
            EventBooking.status == 'Approved',
            EventBooking.start_date <= end_date,
            EventBooking.end_date >= start_date,
            EventBooking.start_time < end_time,
            EventBooking.end_time > start_time
        ).all()
        
        req_room_ids = set()
        if b_type == 'floors':
            rooms = Room.query.join(Floor).filter(Floor.level.in_(targets)).all()
            req_room_ids.update(r.id for r in rooms)
        else:
            req_room_ids.update(targets)
            
        for ev in overlap_events:
            ev_room_ids = set(ev.get_all_target_room_ids())
            if not req_room_ids.isdisjoint(ev_room_ids):
                return api_response(success=False, error=f"Conflict detected with approved event: {ev.title}", status=409)
                
        new_event = EventBooking(
            title=title,
            description=desc,
            faculty_id=session.get('user_id'),
            booking_type=b_type,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            status='Pending'
        )
        
        db.session.add(new_event)
        
        if b_type == 'floors':
            db.session.flush() 
            from ...models import event_floors
            db.session.execute(event_floors.insert().values([
                {'event_id': new_event.id, 'floor_number': t} for t in targets
            ]))
        else:
            rooms = Room.query.filter(Room.id.in_(targets)).all()
            new_event.rooms.extend(rooms)
            
        admins = User.query.filter_by(role=User.ROLE_ADMIN).all()
        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                recipient_role='admin',
                title="New Event Request",
                message=f"{session.get('user_name')} requested an event: {title}.",
                type='event_request',
                link='/admin/events'
            )
            db.session.add(notif)
            
        db.session.commit()
        
        from ...realtime import trigger_event
        trigger_event('admin-notifications', 'new-event-request', {
            'title': title,
            'faculty': session.get('user_name')
        })
        
        return api_response(success=True, message="Event request submitted successfully.")
    except Exception as e:
        logger.error(f"Event booking error: {e}")
        db.session.rollback()
        return api_response(success=False, error="Internal server error", status=500)
