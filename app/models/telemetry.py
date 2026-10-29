"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class BugReport(db.Model):
    """BugReport model for tracking issues reported by users."""
    __tablename__ = 'bug_reports'
    
    STATUS_OPEN = 'open'
    STATUS_RESOLVED = 'resolved'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    file_data = db.Column(db.Text, nullable=True) # base64 file data for serverless (Vercel) persistence
    status = db.Column(db.String(20), default=STATUS_OPEN, nullable=False)
    
    # Optional metadata about who reported it
    reporter_id = db.Column(db.Integer, nullable=True)
    reporter_type = db.Column(db.String(50), nullable=True)  # 'user', 'professional', 'superadmin', 'guest'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, title=None, description=None, file_path=None, file_data=None, status=STATUS_OPEN, reporter_id=None, reporter_type=None, **kwargs):
        super().__init__(**kwargs)
        if title is not None: self.title = title
        if description is not None: self.description = description
        if file_path is not None: self.file_path = file_path
        if file_data is not None: self.file_data = file_data
        if status is not None: self.status = status
        if reporter_id is not None: self.reporter_id = reporter_id
        if reporter_type is not None: self.reporter_type = reporter_type
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_data': self.file_data,
            'status': self.status,
            'reporter_id': self.reporter_id,
            'reporter_type': self.reporter_type,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
