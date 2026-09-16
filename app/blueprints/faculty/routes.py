"""
Faculty Routes Blueprint - Smart Room Scheduling
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from ... import db
from ...models import User, Building, Floor, Room, AdHocBooking, Timetable, RoomBooking
from ...decorators import faculty_login_required
from ...api_utils import handle_api_errors, api_response
from ...realtime import emit_room_status_change

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard')
@faculty_login_required
def dashboard():
    """Faculty combined dashboard (My Schedule & Room Utilization Tracker)."""
    user_id = session.get('user_id')
    faculty = User.query.get(user_id)
    
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
    
    # 2. Room Utilization Tracker (Global View)
    vyas = Building.query.filter_by(name='Vyas').first()
    floors = []
    if vyas:
        floors = Floor.query.filter(Floor.building_id == vyas.id).order_by(Floor.level).all()
        
    # Eager load rooms for efficiency
    all_rooms = Room.query.options(
        joinedload(Room.timetables),
        joinedload(Room.adhoc_bookings).joinedload(AdHocBooking.faculty)
    ).all()
    
    rooms_by_floor = {}
    for room in all_rooms:
        if room.floor_id not in rooms_by_floor:
            rooms_by_floor[room.floor_id] = []
        rooms_by_floor[room.floor_id].append(room)

    # 3. Booking History
    booking_history = RoomBooking.query.filter_by(faculty_id=faculty.id).order_by(RoomBooking.slot_start.desc()).all()

    # Bookings this week for the timetable grid
    start_of_week = (current_dt - timedelta(days=current_day)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    bookings_this_week = RoomBooking.query.filter(
        RoomBooking.faculty_id == faculty.id,
        RoomBooking.status == RoomBooking.STATUS_ACTIVE,
        RoomBooking.slot_start >= start_of_week,
        RoomBooking.slot_start <= end_of_week
    ).all()

    return render_template('faculty/dashboard.html',
                           faculty=faculty,
                           floors=floors,
                           all_rooms=all_rooms,
                           all_faculties=all_faculties,
                           rooms_by_floor=rooms_by_floor,
                           my_schedules=my_schedules,
                           my_adhoc=my_adhoc,
                           booking_history=booking_history,
                           bookings_this_week=bookings_this_week,
                           current_day=current_day,
                           current_user_id=user_id)


@faculty_bp.route('/api/claim-room', methods=['POST'])
@faculty_login_required
@handle_api_errors
def claim_room():
    """Ad-hoc claim of an empty room by faculty."""
    data = request.get_json()
    room_id = data.get('room_id')
    duration_mins = data.get('duration_mins', 60)
    subject = data.get('subject', 'Ad-hoc Lecture').strip()
    
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
    
    # Check if the room is vacant
    status_info = room.current_occupancy_status
    if status_info['status'] == 'occupied':
        return api_response(success=False, error=f"Room is already occupied by {status_info.get('faculty')} for {status_info.get('subject')}.", status=400)
    
    # Calculate UTC start and end
    start_utc = datetime.utcnow()
    end_utc = start_utc + timedelta(minutes=duration_mins)
    
    # Ensure they aren't claiming and conflicting with an upcoming schedule within the duration
    current_dt = start_utc + timedelta(hours=5, minutes=30)
    current_day = current_dt.weekday()
    end_dt_ist = end_utc + timedelta(hours=5, minutes=30)
    
    for sched in room.timetables:
        if sched.day_of_week == current_day:
            sched_start = datetime.combine(current_dt.date(), sched.start_time)
            # If the scheduled lesson starts within our selected duration
            if current_dt < sched_start < end_dt_ist:
                # Truncate the duration or deny
                return api_response(success=False, error=f"Time conflict. A scheduled class for {sched.subject} starts at {sched.start_time.strftime('%I:%M %p')}.", status=400)
    
    user_id = session.get('user_id')
    faculty = User.query.get(user_id)
    
    booking = AdHocBooking(
        room_id=room.id,
        faculty_id=user_id,
        subject=subject,
        start_datetime=start_utc,
        end_datetime=end_utc
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
    

@faculty_bp.route('/api/map/status/<int:floor_id>')
@faculty_login_required
@handle_api_errors
def get_map_status(floor_id):
    """Returns room data for the selected floor in a standard map-ready format."""
    floor = Floor.query.get_or_404(floor_id)
    rooms = Room.query.filter_by(floor_id=floor_id).all()
    
    return api_response(data={
        'floor': {
            'id': floor.id,
            'name': floor.name,
            'level': floor.level
        },
        'rooms': [room.to_map_dict() for room in rooms]
    })


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
            
            # RoomBooking conflict
            existing_booking = RoomBooking.query.filter_by(
                room_id=room_id,
                date=booking_date,
                slot_start=current_slot,
                status=RoomBooking.STATUS_ACTIVE
            ).first()
            
            if existing_booking:
                return api_response(success=False, error=f"Room is already booked for the {current_slot.strftime('%I:%M %p')} slot.", status=400)
                
            # Timetable conflict
            existing_timetable = Timetable.query.filter_by(
                room_id=room_id,
                day_of_week=current_day,
                start_time=current_slot.time()
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
        room = Room.query.get(room_id)
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


@faculty_bp.route('/api/bookings/cancel/<int:booking_id>', methods=['POST'])
@faculty_login_required
@handle_api_errors
def cancel_booking(booking_id):
    """Cancels a faculty booking if they are the owner."""
    booking = RoomBooking.query.get_or_404(booking_id)
    user_id = session.get('user_id')
    
    if booking.faculty_id != user_id:
        return api_response(success=False, error="You can only cancel your own reservations.", status=403)
        
    booking.status = RoomBooking.STATUS_CANCELLED
    db.session.commit()
    
    # Update map for everyone
    emit_room_status_change(booking.room, booking.room.current_occupancy_status)
    
    return api_response(success=True, message="Reservation cancelled successfully.")


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


@faculty_bp.route('/api/faculty/timetable', methods=['POST'])
@faculty_login_required
@handle_api_errors
def upsert_timetable():
    """Bulk upserts timetable entries for the logged-in faculty."""
    data = request.get_json() # Expecting a list of objects
    if not isinstance(data, list):
        return api_response(success=False, error="Data must be a list of timetable entries.", status=400)
        
    user_id = session.get('user_id')
    
    # For simplicity, we'll clear existing timetable for this faculty or handle updates
    # The request says "Bulk upserts", I'll implement a basic upsert
    success_count = 0
    for entry in data:
        room_id = entry.get('room_id')
        day = entry.get('day_of_week')
        start_time_str = entry.get('start_time') # 'HH:MM'
        subject = entry.get('subject')
        duration = int(entry.get('duration', 1))
        collaborator_id = entry.get('collaborator_id')
        if collaborator_id == '': collaborator_id = None
        
        if not all([room_id, day is not None, start_time_str, subject]):
            continue
            
        try:
            start_dt = datetime.strptime(start_time_str, '%H:%M')
            start_time = start_dt.time()
            end_time = (start_dt + timedelta(hours=duration)).time()
        except Exception as e:
            print(f"Error parsing time: {e}")
            continue
            
        # Check for existing entry for this faculty at this time/day to avoid duplicates
        existing = Timetable.query.filter_by(
            faculty_id=user_id,
            day_of_week=day,
            start_time=start_time
        ).first()
        
        if existing:
            # Update
            existing.room_id = room_id
            existing.subject = subject
            existing.end_time = end_time
            existing.collaborator_id = collaborator_id
        else:
            # Create
            new_entry = Timetable(
                room_id=room_id,
                faculty_id=user_id,
                collaborator_id=collaborator_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                subject=subject
            )
            db.session.add(new_entry)
        
        success_count += 1
        
    db.session.commit()
    return api_response(message=f"Successfully synchronized {success_count} entries to your timetable.")


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
        if ampm == 'pm' and hr < 12:
            hr += 12
        elif ampm == 'am' and hr == 12:
            hr = 0
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
        dt_end += timedelta(days=1)
    duration = int(round((dt_end - dt_st).total_seconds() / 3600))
    if duration <= 0:
        duration = 1
    return st_time, end_time, duration


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
                    subj = row[c_idx].strip()
                    if subj and subj.upper() not in ['-', 'N/A', 'NA', 'FREE', 'OFF', 'N/L', 'BREAK', 'LUNCH']:
                        parsed_entries.append({
                            'room_id': room_obj.id,
                            'room_number': room_obj.number,
                            'day_of_week': day_num,
                            'day_name': DAY_NAMES[day_num],
                            'start_time': start_t.strftime('%H:%M'),
                            'end_time': end_t.strftime('%H:%M'),
                            'duration': duration,
                            'subject': subj
                        })
        else:
            day_val = row[day_single_col_idx].strip().lower() if day_single_col_idx != -1 and day_single_col_idx < len(row) else ''
            subj_val = row[subject_col_idx].strip() if subject_col_idx != -1 and subject_col_idx < len(row) else ''
            
            if not subj_val or subj_val.upper() in ['-', 'N/A', 'NA', 'FREE', 'OFF', 'N/L', 'BREAK', 'LUNCH']:
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

            parsed_entries.append({
                'room_id': room_obj.id,
                'room_number': room_obj.number,
                'day_of_week': day_num,
                'day_name': DAY_NAMES[day_num],
                'start_time': start_t.strftime('%H:%M'),
                'end_time': end_t.strftime('%H:%M'),
                'duration': duration,
                'subject': subj_val
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

    admin_user_id = session.get('user_id')
    success_count = 0

    for entry in entries:
        room_id = entry.get('room_id')
        day = entry.get('day_of_week')
        start_time_str = entry.get('start_time')
        subject = entry.get('subject')
        duration = int(entry.get('duration', 1))
        fac_id = entry.get('faculty_id') or admin_user_id

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
            existing.end_time = end_time
            existing.faculty_id = fac_id
        else:
            new_entry = Timetable(
                room_id=room_id,
                faculty_id=fac_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                subject=subject
            )
            db.session.add(new_entry)

        success_count += 1

    db.session.commit()
    return api_response(success=True, message=f"Successfully imported {success_count} timetable records into building schedule.")


