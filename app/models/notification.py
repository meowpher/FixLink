"""
SQLAlchemy Domain Model Module for FixLink
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Notification(db.Model):
    """Notification model - persistent alerts for users (Admins/Professionals)."""
    __tablename__ = 'notifications'
    
    TYPE_CANCELLATION = 'cancellation'
    TYPE_ASSIGNMENT = 'assignment'
    TYPE_HELP = 'help'
    TYPE_CHAT = 'chat'
    TYPE_SYSTEM = 'system'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_role = db.Column(db.String(30), nullable=False, server_default='admin')
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default=TYPE_SYSTEM)
    link = db.Column(db.String(255), nullable=True) # URL or route to follow
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_notif_user_read', 'user_id', 'is_read'),
    )
    
    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
    
    @property
    def recipient_id(self):
        return self.user_id
        
    @recipient_id.setter
    def recipient_id(self, value):
        self.user_id = value
        
    @property
    def category(self):
        return self.type
        
    @category.setter
    def category(self, value):
        self.type = value

    def __init__(self, user_id=None, title=None, message=None, type=TYPE_SYSTEM, link=None, recipient_role='admin', recipient_id=None, category=None, **kwargs):
        super().__init__(**kwargs)
        if recipient_id is not None:
            self.user_id = recipient_id
        elif user_id is not None:
            self.user_id = user_id
            
        if category is not None:
            self.type = category
        elif type is not None:
            self.type = type
            
        if title is not None: self.title = title
        if message is not None: self.message = message
        if link is not None: self.link = link
        if recipient_role is not None: self.recipient_role = recipient_role
        
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Notification #{self.id} for User {self.user_id} - {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

class PushSubscription(db.Model):
    """Stores Web Push API subscriptions for native notifications."""
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, endpoint=None, p256dh=None, auth=None, user_id=None, professional_id=None, **kwargs):
        super().__init__(**kwargs)
        if endpoint is not None: self.endpoint = endpoint
        if p256dh is not None: self.p256dh = p256dh
        if auth is not None: self.auth = auth
        if user_id is not None: self.user_id = user_id
        if professional_id is not None: self.professional_id = professional_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth
            }
        }
