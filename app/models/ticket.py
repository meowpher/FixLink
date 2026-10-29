"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Ticket(db.Model):
    """Ticket model - maintenance requests."""
    __tablename__ = 'tickets'
    
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_FIXED = 'fixed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_ASSIGNED = 'assigned'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    
    STATUS_CHOICES = [STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_FIXED, STATUS_CANCELLED, STATUS_ASSIGNED, STATUS_RESOLVED, STATUS_CLOSED]
    
    COMPLEXITY_LOW = 'low'
    COMPLEXITY_MEDIUM = 'medium'
    COMPLEXITY_HIGH = 'high'
    
    COMPLEXITY_CHOICES = [COMPLEXITY_LOW, COMPLEXITY_MEDIUM, COMPLEXITY_HIGH]
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    
    # Assignment to professional / vendor (Non-authenticated reference for on-ground staff)
    assigned_professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    assigned_vendor_or_tech_name = db.Column(db.String(150), nullable=True)
    
    # Supervisor QA Verification & Closure Tracking (QA Architecture Upgrade)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_by = db.relationship('User', foreign_keys=[verified_by_id], backref=db.backref('verified_tickets', lazy=True))
    proof_image_url = db.Column(db.String(500), nullable=True)
    proof_of_completion_url = db.Column(db.String(500), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    issue_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Complexity (selected by professional)
    complexity = db.Column(db.String(20), nullable=True)
    
    # Time limit set by admin
    time_limit_hours = db.Column(db.Integer, nullable=True)
    deadline_datetime = db.Column(db.DateTime, nullable=True)
    
    # Job tracking
    job_started_at = db.Column(db.DateTime, nullable=True)
    job_completed_at = db.Column(db.DateTime, nullable=True)
    completion_photo_filename = db.Column(db.String(255), nullable=True)
    
    # Cancellation tracking
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by_professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    
    # Reporter info
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reporter_name = db.Column(db.String(100), nullable=False)
    prn = db.Column(db.String(20), nullable=False)
    reporter_email = db.Column(db.String(120), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), default=STATUS_OPEN, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fixed_at = db.Column(db.DateTime, nullable=True)
    last_notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Rating tracking
    rating = db.Column(db.Integer, nullable=True)
    rating_comment = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        db.Index('idx_ticket_status_created', 'status', 'created_at'),
        db.Index('idx_ticket_reporter_created', 'reporter_id', 'created_at'),
        db.Index('idx_ticket_professional_status', 'assigned_professional_id', 'status'),
        db.Index('idx_ticket_room_status', 'room_id', 'status'),
    )
    
    def __init__(self, room_id=None, asset_id=None, issue_type=None, description=None, 
                 image_filename=None, reporter_id=None, reporter_name=None, prn=None, 
                 reporter_email=None, status=STATUS_OPEN, complexity=None, 
                 time_limit_hours=None, deadline_datetime=None, assigned_professional_id=None, **kwargs):
        super().__init__(**kwargs)
        if room_id is not None: self.room_id = room_id
        if asset_id is not None: self.asset_id = asset_id
        if issue_type is not None: self.issue_type = issue_type
        if description is not None: self.description = description
        if image_filename is not None: self.image_filename = image_filename
        if reporter_id is not None: self.reporter_id = reporter_id
        if reporter_name is not None: self.reporter_name = reporter_name
        if prn is not None: self.prn = prn
        if reporter_email is not None: self.reporter_email = reporter_email
        if status is not None: self.status = status
        if complexity is not None: self.complexity = complexity
        if time_limit_hours is not None: self.time_limit_hours = time_limit_hours
        if deadline_datetime is not None: self.deadline_datetime = deadline_datetime
        if assigned_professional_id is not None: self.assigned_professional_id = assigned_professional_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Ticket #{self.id} - {self.status}>'
    
    @property
    def is_overdue(self):
        """Check if ticket deadline has passed."""
        if self.deadline_datetime and self.status not in [self.STATUS_FIXED, self.STATUS_CANCELLED]:
            return datetime.utcnow() > self.deadline_datetime
        return False
    
    @property
    def time_remaining(self):
        """Get time remaining for the task."""
        if self.deadline_datetime and self.status not in [self.STATUS_FIXED, self.STATUS_CANCELLED]:
            remaining = self.deadline_datetime - datetime.utcnow()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f"{hours}h {minutes}m"
            return "Overdue"
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'room_number': self.room.number if self.room else None,
            'room_floor_id': self.room.floor_id if self.room else None,
            'floor_name': self.room.floor.name if self.room and self.room.floor else None,
            'asset_id': self.asset_id,
            'asset_name': self.asset.name if self.asset else None,
            'assigned_professional_id': self.assigned_professional_id,
            'assigned_professional_name': self.assigned_professional.name if self.assigned_professional else None,
            'assigned_professional_category': self.assigned_professional.category if self.assigned_professional else None,
            'cancelled_by_professional_id': self.cancelled_by_professional_id,
            'cancelled_by_professional_name': self.cancelled_by_professional.name if self.cancelled_by_professional else None,
            'cancelled_by_professional_category': self.cancelled_by_professional.category if self.cancelled_by_professional else None,
            'issue_type': self.issue_type,
            'description': self.description,
            'image_filename': self.image_filename,
            'complexity': self.complexity,
            'time_limit_hours': self.time_limit_hours,
            'deadline_datetime': self.deadline_datetime.isoformat() + 'Z' if self.deadline_datetime else None,
            'job_started_at': self.job_started_at.isoformat() + 'Z' if self.job_started_at else None,
            'job_completed_at': self.job_completed_at.isoformat() + 'Z' if self.job_completed_at else None,
            'completion_photo_filename': self.completion_photo_filename,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_at': self.cancelled_at.isoformat() + 'Z' if self.cancelled_at else None,
            'reporter_name': self.reporter_name,
            'prn': self.prn,
            'reporter_email': self.reporter_email,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
            'fixed_at': self.fixed_at.isoformat() + 'Z' if self.fixed_at else None,
            'is_overdue': self.is_overdue,
            'time_remaining': self.time_remaining,
            'rating': self.rating,
            'rating_comment': self.rating_comment,
            'assigned_vendor_or_tech_name': self.assigned_vendor_or_tech_name,
            'verified_by_id': self.verified_by_id,
            'verified_by_name': self.verified_by.name if self.verified_by else None,
            'proof_image_url': self.proof_image_url or self.proof_of_completion_url,
            'proof_of_completion_url': self.proof_of_completion_url or self.proof_image_url,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() + 'Z' if self.resolved_at else None
        }

class AuditLog(db.Model):
    """System Audit Log for security and quality assurance events."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.Text, nullable=False)

    # Backwards-compatible aliases / legacy columns
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = db.relationship('Ticket', foreign_keys=[ticket_id], backref=db.backref('audit_logs', lazy=True))
    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref=db.backref('performed_audit_logs', lazy=True))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('audit_logs', lazy=True))

    def __init__(self, action=None, details=None, ticket_id=None, performed_by_id=None, user_id=None, target_type=None, target_id=None, timestamp=None, created_at=None, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.details = details
        resolved_ticket_id = ticket_id if ticket_id is not None else (target_id if target_type == 'Ticket' else None)
        self.ticket_id = resolved_ticket_id
        self.target_id = target_id if target_id is not None else resolved_ticket_id
        if not target_type and resolved_ticket_id is not None:
            self.target_type = 'Ticket'
        else:
            self.target_type = target_type
        
        resolved_user_id = performed_by_id if performed_by_id is not None else user_id
        self.performed_by_id = resolved_user_id
        self.user_id = resolved_user_id
        
        ts = timestamp or created_at or datetime.utcnow()
        self.timestamp = ts
        self.created_at = ts

    @property
    def related_ticket(self):
        """Resolve ticket relationship safely even for legacy logs with target_type='Ticket'."""
        if self.ticket:
            return self.ticket
        if self.target_type == 'Ticket' and self.target_id:
            from app.models.ticket import Ticket
            return db.session.get(Ticket, self.target_id)
        return None

    def __repr__(self):
        return f'<AuditLog #{self.id} - {self.action} (Ticket #{self.ticket_id})>'

    def to_dict(self):
        user_actor = self.performed_by or self.user
        rel_ticket = getattr(self, '_resolved_ticket', None) or self.related_ticket
        ticket_id = self.ticket_id or (self.target_id if self.target_type == 'Ticket' else None)
        proof_url = (rel_ticket.proof_of_completion_url or rel_ticket.proof_image_url) if rel_ticket else None
        supervisor_name = (rel_ticket.verified_by.name if (rel_ticket and rel_ticket.verified_by) else (user_actor.name if user_actor else None))
        return {
            'id': self.id,
            'ticket_id': ticket_id,
            'action': self.action,
            'performed_by_id': self.performed_by_id or self.user_id,
            'user_id': self.user_id or self.performed_by_id,
            'user_name': user_actor.name if user_actor else None,
            'user_role': getattr(user_actor, 'role', 'ADMIN') if user_actor else None,
            'timestamp': (self.timestamp or self.created_at).isoformat() + 'Z' if (self.timestamp or self.created_at) else None,
            'created_at': (self.created_at or self.timestamp).isoformat() + 'Z' if (self.created_at or self.timestamp) else None,
            'details': self.details,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'proof_url': proof_url,
            'resolution_notes': rel_ticket.resolution_notes if rel_ticket else None,
            'supervisor_name': supervisor_name,
            'ticket_issue_type': rel_ticket.issue_type if rel_ticket else None,
            'ticket_resolved_at': rel_ticket.resolved_at.isoformat() + 'Z' if (rel_ticket and rel_ticket.resolved_at) else None
        }
