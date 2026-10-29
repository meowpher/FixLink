"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """User model - strict 3-Tier RBAC: FACULTY, SUPERVISOR, SUPER_ADMIN."""
    __tablename__ = 'users'
    
    ROLE_FACULTY = 'FACULTY'
    ROLE_SUPERVISOR = 'SUPERVISOR'
    ROLE_ADMIN = 'ADMIN'
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    
    # Backwards-compatible aliases
    ROLE_STUDENT = 'student'
    
    ROLES = [ROLE_FACULTY, ROLE_SUPERVISOR, ROLE_ADMIN]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prn = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default=ROLE_FACULTY, nullable=False)
    designation = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)  # uploaded avatar filename
    adhoc_suspended_until = db.Column(db.DateTime, nullable=True)  # 3-Strike Accountability 7-day lockout
    adhoc_suspension_reason = db.Column(db.String(255), nullable=True)
    has_accepted_terms = db.Column(db.Boolean, default=False, server_default='false', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='reporter', lazy=True, foreign_keys='Ticket.reporter_id')
    
    def __init__(self, name=None, email=None, role=ROLE_FACULTY, prn=None, designation=None, is_active=True, is_admin=False, is_verified=False, verification_token=None, profile_photo=None, adhoc_suspended_until=None, adhoc_suspension_reason=None, has_accepted_terms=False, **kwargs):
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if designation is not None:
            self.designation = designation
        self.is_active = is_active
        if role is not None:
            role_str = str(role).strip().upper()
            if role_str == 'STUDENT':
                self.role = 'student'
            elif role_str == 'FACULTY':
                self.role = self.ROLE_FACULTY
            elif role_str == 'SUPERVISOR':
                self.role = self.ROLE_SUPERVISOR
            elif role_str == 'ADMIN':
                self.role = self.ROLE_ADMIN
            elif role_str in ['SUPERADMIN', 'SUPER_ADMIN']:
                self.role = self.ROLE_SUPER_ADMIN
            else:
                self.role = role_str
        else:
            self.role = self.ROLE_FACULTY
        if prn is not None:
            self.prn = prn
        self.is_admin = is_admin or (str(self.role or '').upper() in [self.ROLE_SUPERVISOR, self.ROLE_ADMIN, self.ROLE_SUPER_ADMIN, 'ADMIN', 'SUPERVISOR'])
        self.is_verified = is_verified
        self.has_accepted_terms = has_accepted_terms
        if verification_token is not None:
            self.verification_token = verification_token
        if profile_photo is not None:
            self.profile_photo = profile_photo
        if adhoc_suspended_until is not None:
            self.adhoc_suspended_until = adhoc_suspended_until
        if adhoc_suspension_reason is not None:
            self.adhoc_suspension_reason = adhoc_suspension_reason
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Hash is malformed/unsupported — deny access rather than fall back to plain-text
            return False

    @property
    def is_adhoc_suspended(self):
        """Returns True if the user is currently under a 3-Strike 7-day lockout."""
        if not self.adhoc_suspended_until:
            return False
        return self.adhoc_suspended_until > datetime.utcnow()
        
    @property
    def suspension_remaining_str(self):
        """Human-readable time remaining on adhoc booking suspension."""
        if not self.is_adhoc_suspended:
            return None
        diff = self.adhoc_suspended_until - datetime.utcnow()
        days = diff.days
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h remaining"
        elif hours > 0:
            return f"{hours}h {mins}m remaining"
        else:
            return f"{mins}m remaining"



    @property
    def is_faculty(self):
        """Returns True if the user has FACULTY role."""
        return (self.role or '').upper() in [self.ROLE_FACULTY, 'STUDENT']

    @property
    def is_supervisor(self):
        """Returns True if the user has SUPERVISOR or SUPER_ADMIN role, or is_admin flag."""
        return (self.role or '').upper() in [self.ROLE_SUPERVISOR, self.ROLE_SUPER_ADMIN, 'ADMIN'] or self.is_admin or self.is_super_admin

    @property
    def is_super_admin(self):
        """Dynamic check against hardcoded config or strict SUPER_ADMIN role."""
        if not self.email:
            return False
        if (self.role or '').upper() == self.ROLE_SUPER_ADMIN:
            return True
        from app import SUPER_ADMIN_EMAILS
        normalized_email = self.email.strip().lower()
        return normalized_email in [admin_email.strip().lower() for admin_email in SUPER_ADMIN_EMAILS]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'prn': self.prn,
            'role': self.role,
            'designation': self.designation,
            'is_active': self.is_active,
            'is_faculty': self.is_faculty,
            'is_supervisor': self.is_supervisor,
            'is_admin': self.is_admin or self.is_supervisor,
            'is_super_admin': self.is_super_admin,
            'is_verified': self.is_verified,
            'has_accepted_terms': self.has_accepted_terms,
            'is_adhoc_suspended': self.is_adhoc_suspended,
            'adhoc_suspended_until': self.adhoc_suspended_until.isoformat() + 'Z' if self.adhoc_suspended_until else None,
            'suspension_remaining': self.suspension_remaining_str,
            'photo_url': self.profile_photo,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class NoShowStrike(db.Model):
    """Tracks Ghost Protocol no-show auto-cancellations for the 3-Strike Accountability Engine."""
    __tablename__ = 'noshow_strikes'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    strike_reason = db.Column(db.String(255), default='Ghost Protocol: 10-Minute Check-In Timeout')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    faculty = db.relationship('User', backref=db.backref('noshow_strikes', lazy=True, cascade='all, delete-orphan'))
    room = db.relationship('Room', lazy=True)
    
    def __init__(self, faculty_id=None, booking_id=None, room_id=None, strike_reason=None, **kwargs):
        super().__init__(**kwargs)
        if faculty_id is not None: self.faculty_id = faculty_id
        if booking_id is not None: self.booking_id = booking_id
        if room_id is not None: self.room_id = room_id
        if strike_reason is not None: self.strike_reason = strike_reason
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'booking_id': self.booking_id,
            'room_id': self.room_id,
            'strike_reason': self.strike_reason,
            'created_at': self.created_at.isoformat() + 'Z'
        }

class SuspensionLog(db.Model):
    """Permanent audit log of every Ghost Protocol suspension event — never deleted."""
    __tablename__ = 'suspension_logs'

    EVENT_SUSPENDED = 'suspended'
    EVENT_LIFTED    = 'lifted'
    EVENT_EXPIRED   = 'expired'

    id             = db.Column(db.Integer, primary_key=True)
    faculty_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type     = db.Column(db.String(20), nullable=False)          # suspended / lifted / expired
    reason         = db.Column(db.String(512), nullable=True)          # why triggered / lift note
    suspended_until= db.Column(db.DateTime, nullable=True)             # when the ban was set to expire
    strike_count   = db.Column(db.Integer, default=0, nullable=False)  # rolling-30d strikes at event time
    lifted_by_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # admin who lifted
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    faculty   = db.relationship('User', foreign_keys=[faculty_id],
                                backref=db.backref('suspension_logs', lazy=True, cascade='all, delete-orphan'))
    lifted_by = db.relationship('User', foreign_keys=[lifted_by_id], lazy=True)

    def __init__(self, faculty_id=None, event_type=None, reason=None, suspended_until=None, strike_count=0, lifted_by_id=None, **kwargs):
        super().__init__(**kwargs)
        if faculty_id is not None: self.faculty_id = faculty_id
        if event_type is not None: self.event_type = event_type
        if reason is not None: self.reason = reason
        if suspended_until is not None: self.suspended_until = suspended_until
        if strike_count is not None: self.strike_count = strike_count
        if lifted_by_id is not None: self.lifted_by_id = lifted_by_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<SuspensionLog {self.event_type} faculty={self.faculty_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'event_type': self.event_type,
            'reason': self.reason,
            'suspended_until': self.suspended_until.isoformat() + 'Z' if self.suspended_until else None,
            'strike_count': self.strike_count,
            'lifted_by_id': self.lifted_by_id,
            'created_at': self.created_at.isoformat() + 'Z'
        }
