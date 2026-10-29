"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class AdHocBooking(db.Model):
    """AdHocBooking model - Instant claims for vacant rooms by faculty."""
    __tablename__ = 'adhoc_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False) # Stored in UTC
    end_datetime = db.Column(db.DateTime, nullable=False)   # Stored in UTC
    checked_in = db.Column(db.Boolean, default=False, nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    faculty = db.relationship('User', backref='adhoc_bookings', lazy=True)
    
    def __init__(self, room_id=None, faculty_id=None, subject=None, start_datetime=None, end_datetime=None, checked_in=False, checked_in_at=None, **kwargs):
        super().__init__(**kwargs)
        if room_id is not None: self.room_id = room_id
        if faculty_id is not None: self.faculty_id = faculty_id
        if subject is not None: self.subject = subject
        if start_datetime is not None: self.start_datetime = start_datetime
        if end_datetime is not None: self.end_datetime = end_datetime
        if checked_in is not None: self.checked_in = checked_in
        if checked_in_at is not None: self.checked_in_at = checked_in_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.name if self.faculty else 'Unknown',
            'subject': self.subject,
            'start_datetime': self.start_datetime.isoformat() + 'Z',
            'end_datetime': self.end_datetime.isoformat() + 'Z',
            'checked_in': self.checked_in,
            'checked_in_at': self.checked_in_at.isoformat() + 'Z' if self.checked_in_at else None
        }

class Timetable(db.Model):
    """Timetable model - Weekly recurring faculty schedule in 1-hour blocks."""
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    collaborator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False) # 0=Mon, ..., 6=Sun
    start_time = db.Column(db.Time, nullable=False) # e.g., 10:00
    end_time = db.Column(db.Time, nullable=False)   # e.g., 12:00
    subject = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=True)
    division = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_timetable_lookup', 'faculty_id', 'day_of_week', 'start_time'),
        db.Index('idx_timetable_collab', 'collaborator_id', 'day_of_week', 'start_time'),
        db.Index('idx_timetable_room', 'room_id', 'day_of_week', 'start_time'),
    )
    
    faculty = db.relationship('User', foreign_keys=[faculty_id], backref=db.backref('timetables', lazy=True))
    collaborator = db.relationship('User', foreign_keys=[collaborator_id], backref=db.backref('collaborated_timetables', lazy=True))
    
    def __init__(self, faculty_id=None, collaborator_id=None, room_id=None, day_of_week=None, start_time=None, end_time=None, subject=None, course=None, division=None, **kwargs):
        super().__init__(**kwargs)
        if faculty_id is not None: self.faculty_id = faculty_id
        if collaborator_id is not None: self.collaborator_id = collaborator_id
        if room_id is not None: self.room_id = room_id
        if day_of_week is not None: self.day_of_week = day_of_week
        if start_time is not None: self.start_time = start_time
        if end_time is not None: self.end_time = end_time
        if subject is not None: self.subject = subject
        if course is not None: self.course = course
        if division is not None: self.division = division
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.name if self.faculty else 'Unassigned',
            'collaborator_id': self.collaborator_id,
            'collaborator_name': self.collaborator.name if self.collaborator else None,
            'room_id': self.room_id,
            'room_number': self.room.number if self.room else 'Unknown',
            'floor_level': self.room.floor.level if self.room and self.room.floor else 4,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'subject': self.subject,
            'course': self.course,
            'division': self.division
        }

class RoomBooking(db.Model):
    """RoomBooking model - Specific 1 or 2 hour slot bookings for faculty."""
    __tablename__ = 'room_bookings'
    
    STATUS_ACTIVE = 'active'
    STATUS_CANCELLED = 'cancelled'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slot_start = db.Column(db.DateTime, nullable=False) # Using DateTime to store timestamp
    status = db.Column(db.String(20), default=STATUS_ACTIVE)
    subject = db.Column(db.String(100), nullable=True)
    division = db.Column(db.String(50), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    checked_in = db.Column(db.Boolean, default=False, nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_booking_status_slot', 'status', 'slot_start'),
        db.Index('idx_booking_faculty_date', 'faculty_id', 'date'),
        db.Index('idx_booking_room_slot', 'room_id', 'status', 'slot_start'),
    )
    
    faculty = db.relationship('User', backref=db.backref('room_bookings', lazy=True))

    def __init__(self, room_id=None, faculty_id=None, date=None, slot_start=None, status=STATUS_ACTIVE, subject=None, division=None, course=None, checked_in=False, checked_in_at=None, **kwargs):
        super().__init__(**kwargs)
        if room_id is not None: self.room_id = room_id
        if faculty_id is not None: self.faculty_id = faculty_id
        if date is not None: self.date = date
        if slot_start is not None: self.slot_start = slot_start
        if status is not None: self.status = status
        if subject is not None: self.subject = subject
        if division is not None: self.division = division
        if course is not None: self.course = course
        if checked_in is not None: self.checked_in = checked_in
        if checked_in_at is not None: self.checked_in_at = checked_in_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def slot_end(self):
        """Returns slot end time (1 hour after slot_start)."""
        return self.slot_start + timedelta(hours=1) if self.slot_start else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'room_number': self.room.number if self.room else None,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.name if self.faculty else 'Unknown',
            'date': self.date.isoformat() if self.date else None,
            'slot_start': self.slot_start.isoformat() + 'Z' if self.slot_start else None,
            'slot_end': self.slot_end.isoformat() + 'Z' if self.slot_end else None,
            'status': self.status,
            'subject': self.subject,
            'division': self.division,
            'course': self.course,
            'checked_in': self.checked_in,
            'checked_in_at': self.checked_in_at.isoformat() + 'Z' if self.checked_in_at else None
        }

class ScheduleSubmission(db.Model):
    """ScheduleSubmission model - Tracks faculty visual timetable submissions for bulk admin approval."""
    __tablename__ = 'schedule_submissions'
    
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUSES = [STATUS_DRAFT, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED]
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    academic_term = db.Column(db.String(50), default='AY 2026-27 Sem 1', nullable=False)
    total_hours = db.Column(db.Integer, default=0, nullable=False)
    schedule_data = db.Column(db.JSON, nullable=False) # List of slot objects
    admin_notes = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_sched_sub_fac_status', 'faculty_id', 'status'),
    )
    
    # Relationships
    faculty = db.relationship('User', foreign_keys=[faculty_id], backref=db.backref('schedule_submissions', lazy=True, cascade='all, delete-orphan'))
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def __init__(self, faculty_id=None, status=STATUS_PENDING, academic_term='AY 2026-27 Sem 1', total_hours=0, schedule_data=None, admin_notes=None, **kwargs):
        super().__init__(**kwargs)
        if faculty_id is not None: self.faculty_id = faculty_id
        if status is not None: self.status = status
        if academic_term is not None: self.academic_term = academic_term
        if total_hours is not None: self.total_hours = total_hours
        self.schedule_data = schedule_data if schedule_data is not None else []
        if admin_notes is not None: self.admin_notes = admin_notes
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.name if self.faculty else 'Unknown',
            'faculty_email': self.faculty.email if self.faculty else None,
            'status': self.status,
            'academic_term': self.academic_term,
            'total_hours': self.total_hours,
            'slot_count': len(self.schedule_data) if isinstance(self.schedule_data, list) else 0,
            'schedule_data': self.schedule_data,
            'admin_notes': self.admin_notes,
            'submitted_at': self.submitted_at.isoformat() + 'Z' if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() + 'Z' if self.reviewed_at else None,
            'reviewed_by_name': self.reviewed_by.name if self.reviewed_by else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

event_rooms = db.Table('event_rooms',
    db.Column('event_id', db.Integer, db.ForeignKey('event_bookings.id', ondelete='CASCADE'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
)

event_floors = db.Table('event_floors',
    db.Column('event_id', db.Integer, db.ForeignKey('event_bookings.id', ondelete='CASCADE'), primary_key=True),
    db.Column('floor_number', db.Integer, primary_key=True)
)

class EventBooking(db.Model):
    __tablename__ = 'event_bookings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    booking_type = db.Column(db.String(20), nullable=False)  # 'rooms' or 'floors'
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    faculty = db.relationship('User', backref='event_bookings')
    rooms = db.relationship('Room', secondary=event_rooms, backref='booked_events')
    
    __table_args__ = (
        db.Index('idx_event_start_end', 'start_date', 'end_date'),
        db.Index('idx_event_status', 'status'),
    )

    def __init__(self, title=None, description=None, faculty_id=None, booking_type='rooms', start_date=None, end_date=None, start_time=None, end_time=None, status='Pending', rejection_reason=None, **kwargs):
        super().__init__(**kwargs)
        if title is not None: self.title = title
        if description is not None: self.description = description
        if faculty_id is not None: self.faculty_id = faculty_id
        if booking_type is not None: self.booking_type = booking_type
        if start_date is not None: self.start_date = start_date
        if end_date is not None: self.end_date = end_date
        if start_time is not None: self.start_time = start_time
        if end_time is not None: self.end_time = end_time
        if status is not None: self.status = status
        if rejection_reason is not None: self.rejection_reason = rejection_reason
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_all_target_room_ids(self):
        if self.booking_type == 'floors':
            from sqlalchemy import select
            floor_levels = [row.floor_number for row in db.session.execute(select(event_floors.c.floor_number).where(event_floors.c.event_id == self.id)).fetchall()]
            from app.models.facility import Room, Floor
            rooms = Room.query.join(Floor).filter(Floor.level.in_(floor_levels)).all()
            return [r.id for r in rooms]
        else:
            return [r.id for r in self.rooms]

    def get_target_rooms(self):
        """Return list of Room objects targeted by this event booking."""
        if self.booking_type == 'floors':
            from sqlalchemy import select
            floor_levels = [row.floor_number for row in db.session.execute(select(event_floors.c.floor_number).where(event_floors.c.event_id == self.id)).fetchall()]
            from app.models.facility import Room, Floor
            return Room.query.join(Floor).filter(Floor.level.in_(floor_levels)).all()
        return self.rooms or []

    def get_target_floors(self):
        """Return list of floor levels targeted by this event booking."""
        if self.booking_type == 'floors':
            from sqlalchemy import select
            return [row.floor_number for row in db.session.execute(select(event_floors.c.floor_number).where(event_floors.c.event_id == self.id)).fetchall()]
        return []
