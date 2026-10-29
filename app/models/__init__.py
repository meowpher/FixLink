"""
FixLink SQLAlchemy Domain Models Package
Decoupled model architecture preserving 100% schema parity.
"""
from app import db
from .user import User, NoShowStrike, SuspensionLog
from .facility import Building, Floor, Room, Asset
from .ticket import Ticket, AuditLog
from .professional import Professional, HelpRequest
from .notification import Notification, PushSubscription
from .schedule import (
    AdHocBooking,
    Timetable,
    RoomBooking,
    ScheduleSubmission,
    EventBooking,
    event_rooms,
    event_floors,
)
from .telemetry import BugReport

__all__ = [
    'User',
    'NoShowStrike',
    'SuspensionLog',
    'Building',
    'Floor',
    'Room',
    'Asset',
    'Ticket',
    'AuditLog',
    'Professional',
    'HelpRequest',
    'Notification',
    'PushSubscription',
    'AdHocBooking',
    'Timetable',
    'RoomBooking',
    'ScheduleSubmission',
    'EventBooking',
    'event_rooms',
    'event_floors',
    'BugReport',
]
