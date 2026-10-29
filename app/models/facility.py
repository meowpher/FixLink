"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Building(db.Model):

    """Building model - Vyas building."""
    __tablename__ = 'buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    floors = db.relationship('Floor', backref='building', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name=None, description=None, **kwargs):
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Building {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

class Floor(db.Model):
    """Floor model - floors in Vyas building (0-7)."""
    __tablename__ = 'floors'
    
    id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 0=Ground, 1-7=Floors
    name = db.Column(db.String(50), nullable=False)  # e.g., '4th Floor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', backref='floor', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, level=None, name=None, building_id=None, building=None, **kwargs):
        super().__init__(**kwargs)
        if level is not None:
            self.level = level
        if name is not None:
            self.name = name
        if building_id is not None:
            self.building_id = building_id
        if building is not None:
            self.building = building
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Floor {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'level': self.level,
            'name': self.name,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

class Room(db.Model):
    """Room model - rooms on each floor."""
    __tablename__ = 'rooms'
    
    ROOM_TYPE_CLASSROOM = 'class'
    ROOM_TYPE_LAB = 'lab'
    ROOM_TYPE_WASHROOM = 'washroom'
    ROOM_TYPE_STORAGE = 'storage'
    ROOM_TYPE_KITCHEN = 'kitchen'
    ROOM_TYPE_BAR = 'bar'
    ROOM_TYPE_CONFERENCE = 'conference_room'
    ROOM_TYPE_MEETING = 'meeting_room'
    ROOM_TYPE_OTHER = 'other'
    
    ROOM_TYPES = [ROOM_TYPE_CLASSROOM, ROOM_TYPE_LAB, ROOM_TYPE_WASHROOM, ROOM_TYPE_STORAGE, ROOM_TYPE_KITCHEN, ROOM_TYPE_BAR, ROOM_TYPE_CONFERENCE, ROOM_TYPE_MEETING, ROOM_TYPE_OTHER]
    
    id = db.Column(db.Integer, primary_key=True)
    floor_id = db.Column(db.Integer, db.ForeignKey('floors.id'), nullable=False)
    number = db.Column(db.String(20), nullable=False)  # e.g., 'VY401'
    name = db.Column(db.String(100), nullable=True)  # e.g., 'Classroom 401'
    room_type = db.Column(db.String(20), default=ROOM_TYPE_CLASSROOM, nullable=False)
    map_coords = db.Column(db.String(255), nullable=True)  # Optional: SVG coords or grid position
    svg_id = db.Column(db.String(50), nullable=True)      # ID of path/rect in SVG file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_room_floor', 'floor_id'),
    )
    
    # Relationships
    assets = db.relationship('Asset', backref='room', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='room', lazy=True)

    adhoc_bookings = db.relationship('AdHocBooking', backref='room', lazy=True, cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', backref='room', lazy=True, cascade='all, delete-orphan')
    room_bookings = db.relationship('RoomBooking', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, number=None, name=None, floor_id=None, floor=None, room_type=ROOM_TYPE_CLASSROOM, map_coords=None, svg_id=None, **kwargs):
        super().__init__(**kwargs)
        if number is not None:
            self.number = number
        if name is not None:
            self.name = name
        if floor_id is not None:
            self.floor_id = floor_id
        if floor is not None:
            self.floor = floor
        if room_type is not None:
            self.room_type = room_type
        if map_coords is not None:
            self.map_coords = map_coords
        if svg_id is not None:
            self.svg_id = svg_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Room {self.number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'floor_id': self.floor_id,
            'number': self.number,
            'name': self.name,
            'room_type': self.room_type,
            'map_coords': self.map_coords,
            'floor_name': self.floor.name if self.floor else None,
            'building_name': self.floor.building.name if self.floor and self.floor.building else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'occupancy_status': self.current_occupancy_status,
            'time_until_next_lecture': self.time_until_next_lecture
        }
    
    @property
    def has_open_tickets(self):
        from app.models.ticket import Ticket
        """Check if room has any OPEN tickets (Red status) using efficient DB query."""
        return Ticket.query.filter_by(room_id=self.id, status=Ticket.STATUS_OPEN).first() is not None
    

    
    @property
    def current_occupancy_status(self):
        """Returns complex dict with Room status based on timetable and bookings."""
        from datetime import datetime, timedelta
        
        now_utc = datetime.utcnow()
        current_hour_start = now_utc.replace(minute=0, second=0, microsecond=0)
        
        # 1. Check active RoomBooking (Specific slot)
        active_booking = None
        for booking in self.room_bookings:
            if booking.status == 'active' and booking.slot_start <= current_hour_start < booking.slot_end:
                active_booking = booking
                break
                
        if active_booking:
            return {
                'status': 'occupied',
                'id': active_booking.id,
                'type': 'booking',
                'subject': active_booking.subject,
                'faculty': active_booking.faculty.name if active_booking.faculty else 'Faculty',
                'faculty_id': active_booking.faculty_id,
                # NOTE: is_owner is intentionally omitted here.
                # It is session-dependent and must be computed client-side
                # to prevent cache poisoning across users.
                'end_time': (active_booking.slot_end + timedelta(hours=5, minutes=30)).strftime('%I:%M %p') # +5:30 for IST
            }

        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        current_date = now_ist.date()
        current_time = now_ist.time().replace(minute=0, second=0, microsecond=0)
            
        # 1.5. Check EventBooking (approved events)
        for ev in self.booked_events:
            if ev.status == 'Approved' and ev.start_date <= current_date <= ev.end_date:
                if ev.start_time <= current_time < ev.end_time:
                    return {
                        'status': 'occupied',
                        'id': ev.id,
                        'type': 'event',
                        'subject': f"Event: {ev.title}",
                        'faculty': ev.faculty.name if ev.faculty else 'Faculty',
                        'faculty_id': ev.faculty_id,
                        'end_time': ev.end_time.strftime('%I:%M %p')
                    }
                    
        # 2. Check Timetable (Recurring schedule)
        current_day = now_ist.weekday()
        
        active_timetable = None
        for tt in self.timetables:
            if tt.day_of_week == current_day:
                # Check if current time is within [start_time, end_time)
                if tt.start_time <= current_time < tt.end_time:
                    active_timetable = tt
                    break
                
        if active_timetable:
            return {
                'status': 'occupied',
                'id': active_timetable.id,
                'type': 'scheduled',
                'subject': active_timetable.subject,
                'faculty': active_timetable.faculty.name if active_timetable.faculty else 'Faculty',
                'faculty_id': active_timetable.faculty_id,
                # NOTE: is_owner is intentionally omitted here.
                # It is session-dependent and must be computed client-side
                # to prevent cache poisoning across users.
                'end_time': (datetime.combine(now_ist.date(), active_timetable.end_time)).strftime('%I:%M %p')
            }
            
        return {'status': 'vacant'}
        
    @property
    def time_until_next_lecture(self):
        """Returns string indicating time till next lecture if vacant."""
        status = self.current_occupancy_status
        if status['status'] == 'occupied':
            return None
            
        from datetime import datetime, timedelta
        current_dt = datetime.utcnow() + timedelta(hours=5, minutes=30)
        current_time = current_dt.time()
        current_day = current_dt.weekday()
        
        # Look for the next timetable entry TODAY
        todays_schedules = [tt for tt in self.timetables if tt.day_of_week == current_day and tt.start_time > current_time]
        todays_schedules.sort(key=lambda tt: tt.start_time)
        
        if todays_schedules:
            next_sched = todays_schedules[0]
            # calculate delta
            next_dt = datetime.combine(current_dt.date(), next_sched.start_time)
            diff = next_dt - current_dt
            minutes = int(diff.total_seconds() / 60)
            if minutes > 60:
                hours = minutes // 60
                mins = minutes % 60
                return f"{hours}h {mins}m"
            return f"{minutes}m"
            
        return "Free for rest of day"

    @property
    def status(self):
        """
        Return room maintenance status using eager loaded collections to avoid N+1 queries.
        - 'issue': Has OPEN tickets or broken assets (Red)
        - 'in-progress': Has IN_PROGRESS tickets (Yellow)
        - 'assigned': Has ASSIGNED tickets but NO open/in-progress (Blue)
        - 'normal': No open, in-progress or assigned tickets (Green)
        """
        return self.compute_status_from_loaded()[0]

    def compute_status_from_loaded(self):
        from app.models.ticket import Ticket
        """
        Compute room status from eagerly-loaded relationships.
        Avoids N+1 queries by reading from already-loaded collections.
        """
        has_open = any(t.status == Ticket.STATUS_OPEN for t in self.tickets)
        has_broken = any(a.status == Asset.STATUS_BROKEN for a in self.assets)
        has_in_progress = any(t.status == Ticket.STATUS_IN_PROGRESS for t in self.tickets)
        has_assigned = any(t.status == Ticket.STATUS_ASSIGNED for t in self.tickets)
        
        if has_open or has_broken:
            return 'issue', has_open, has_broken
        elif has_in_progress:
            return 'in-progress', has_open, has_broken
        elif has_assigned:
            return 'assigned', has_open, has_broken
        return 'normal', has_open, has_broken

    def to_map_dict(self):
        """
        Slim serialization for map rendering with rich timetable and booking schedule data.
        MUST be called after eager-loading tickets and assets.
        """
        from datetime import datetime, timedelta
        status, has_open, has_broken = self.compute_status_from_loaded()
        
        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        current_day = now_ist.weekday()
        current_time = now_ist.time()
        
        # Build today's schedule list
        today_slots = []
        for tt in self.timetables:
            if tt.day_of_week == current_day:
                is_current = (tt.start_time <= current_time < tt.end_time)
                is_past = (tt.end_time <= current_time)
                is_upcoming = (tt.start_time > current_time)
                
                today_slots.append({
                    'id': tt.id,
                    'type': 'timetable',
                    'start_time': tt.start_time.strftime('%I:%M %p') if tt.start_time else '',
                    'end_time': tt.end_time.strftime('%I:%M %p') if tt.end_time else '',
                    'start_raw': tt.start_time.strftime('%H:%M') if tt.start_time else '',
                    'end_raw': tt.end_time.strftime('%H:%M') if tt.end_time else '',
                    'subject': tt.subject,
                    'course': tt.course or '',
                    'division': tt.division or '',
                    'faculty_name': tt.faculty.name if tt.faculty else 'Faculty',
                    'faculty_id': tt.faculty_id,
                    'is_current': is_current,
                    'is_past': is_past,
                    'is_upcoming': is_upcoming
                })
                
        # Also include today's active room bookings
        today_date = now_ist.date()
        for rb in self.room_bookings:
            if rb.status == 'active' and rb.date == today_date:
                rb_start = rb.slot_start + timedelta(hours=5, minutes=30)
                rb_end = rb.slot_end + timedelta(hours=5, minutes=30)
                start_t = rb_start.time()
                end_t = rb_end.time()
                is_current = (start_t <= current_time < end_t)
                is_past = (end_t <= current_time)
                is_upcoming = (start_t > current_time)
                
                today_slots.append({
                    'id': rb.id,
                    'type': 'booking',
                    'start_time': rb_start.strftime('%I:%M %p'),
                    'end_time': rb_end.strftime('%I:%M %p'),
                    'start_raw': rb_start.strftime('%H:%M'),
                    'end_raw': rb_end.strftime('%H:%M'),
                    'subject': rb.subject or 'Reserved Slot',
                    'course': rb.course or '',
                    'division': rb.division or '',
                    'faculty_name': rb.faculty.name if rb.faculty else 'Faculty',
                    'faculty_id': rb.faculty_id,
                    'is_current': is_current,
                    'is_past': is_past,
                    'is_upcoming': is_upcoming
                })
                
        today_slots.sort(key=lambda x: x.get('start_raw', ''))

        # Build full weekly schedule summary grouped by day (0=Mon ... 5=Sat)
        weekly_schedule = {d: [] for d in range(6)}
        for tt in self.timetables:
            if 0 <= tt.day_of_week <= 5:
                weekly_schedule[tt.day_of_week].append({
                    'id': tt.id,
                    'type': 'timetable',
                    'start_time': tt.start_time.strftime('%I:%M %p') if tt.start_time else '',
                    'end_time': tt.end_time.strftime('%I:%M %p') if tt.end_time else '',
                    'start_raw': tt.start_time.strftime('%H:%M') if tt.start_time else '',
                    'end_raw': tt.end_time.strftime('%H:%M') if tt.end_time else '',
                    'subject': tt.subject,
                    'course': tt.course or '',
                    'division': tt.division or '',
                    'faculty_name': tt.faculty.name if tt.faculty else 'Faculty',
                    'faculty_id': tt.faculty_id
                })
        for d in weekly_schedule:
            weekly_schedule[d].sort(key=lambda x: x.get('start_raw', ''))
            
        return {
            'id': self.id,
            'floor_id': self.floor_id,
            'number': self.number,
            'name': self.name,
            'room_type': self.room_type,
            'status': status,
            'has_open_tickets': has_open,
            'has_broken_assets': has_broken,
            'occupancy': self.current_occupancy_status,
            'time_until_next_lecture': self.time_until_next_lecture,
            'today_schedule': today_slots,
            'weekly_schedule': weekly_schedule,
            'total_weekly_slots': sum(len(v) for v in weekly_schedule.values())
        }

class Asset(db.Model):
    """Asset model - equipment in rooms."""
    __tablename__ = 'assets'
    
    STATUS_WORKING = 'working'
    STATUS_BROKEN = 'broken'
    STATUS_MAINTENANCE = 'maintenance'
    
    STATUS_CHOICES = [STATUS_WORKING, STATUS_BROKEN, STATUS_MAINTENANCE]
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # e.g., 'projector', 'ac', 'computer'
    status = db.Column(db.String(20), default=STATUS_WORKING, nullable=False)
    installation_date = db.Column(db.DateTime, default=datetime.utcnow) # Actual date asset was installed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_asset_room_status', 'room_id', 'status'),
    )
    
    # Relationships
    tickets = db.relationship('Ticket', backref='asset', lazy=True)
    
    def __init__(self, name=None, asset_type=None, room_id=None, room=None, status=STATUS_WORKING, installation_date=None, **kwargs):
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        if asset_type is not None:
            self.asset_type = asset_type
        if room_id is not None:
            self.room_id = room_id
        if room is not None:
            self.room = room
        if status is not None:
            self.status = status
        if installation_date is not None:
            self.installation_date = installation_date
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Asset {self.name} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'asset_type': self.asset_type,
            'room_id': self.room_id,
            'status': self.status,
            'installation_date': self.installation_date.isoformat() + 'Z' if self.installation_date else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

    def to_map_dict(self):
        """Slim serialization for map rendering."""
        return {
            'id': self.id,
            'name': self.name,
            'asset_type': self.asset_type,
            'status': self.status,
        }
