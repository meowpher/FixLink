"""
Spam Detection and User Strike Engine for FixLink Maintenance Reports.
Enforces:
1. Maximum Daily Limit: 3 reports per user per calendar day.
2. Spam & Abuse Detection:
   - Rapid-fire submission bursts (< 15 seconds).
   - Duplicate active tickets (same room + issue_type + description within 2 hours).
   - Character repetition spam (e.g., 'aaaaaa', '......', 'asdfasdfasdf').
   - Repetitive word spam (e.g., 'test test test test').
   - Gibberish / keyboard mash detection.
3. Automated Strike Issuance & 3-Strike 14-Day Account Suspension.
"""
import re
from datetime import datetime, timedelta
from flask import current_app
from . import db
from .models import Ticket, NoShowStrike, User

MAX_DAILY_REPORTS = 3
BURST_THRESHOLD_SECONDS = 15
DUPLICATE_WINDOW_HOURS = 2


def get_user_daily_reports_count(user_id, user_email=None):
    """Return the count of tickets submitted by the user today (UTC)."""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
    
    query = Ticket.query.filter(Ticket.created_at >= today_start)
    if user_id and user_email:
        query = query.filter((Ticket.reporter_id == user_id) | (Ticket.reporter_email == user_email.lower()))
    elif user_id:
        query = query.filter(Ticket.reporter_id == user_id)
    elif user_email:
        query = query.filter(Ticket.reporter_email == user_email.lower())
    else:
        return 0
        
    return query.count()


def is_daily_report_limit_exceeded(user):
    """Check if a non-superadmin user has exceeded their daily report limit (Max 3/day)."""
    if not user or user.is_super_admin:
        return False
    
    count = get_user_daily_reports_count(user.id, user.email)
    return count >= MAX_DAILY_REPORTS


def detect_report_spam(user, room_id, issue_type, description):
    """
    Analyzes maintenance report submission for spam patterns.
    Returns: (is_spam: bool, reason: str)
    """
    if not description or not description.strip():
        return True, "Empty report description"
        
    clean_desc = description.strip()
    
    # 1. Minimum meaningful length
    if len(clean_desc) < 3:
        return True, "Description is too short to be a valid maintenance report"
        
    # 2. Check for single character repetition (e.g. 'aaaaaa', '.......', '!!!!!!')
    # If 5+ identical consecutive characters or if a single character represents >= 50% of the text
    if re.search(r'(.)\1{4,}', clean_desc):
        return True, "Repeated character pattern detected"
        
    for char in set(clean_desc):
        if not char.isspace() and (clean_desc.count(char) / len(clean_desc)) > 0.5 and len(clean_desc) >= 6:
            return True, "Excessive single-character spam detected"
            
    # 3. Check for repetitive word spam (e.g. 'test test test test', 'broken broken broken broken')
    if re.search(r'(\b\w+\b)(?:\s+\1){3,}', clean_desc, re.IGNORECASE):
        return True, "Repetitive word spam pattern detected"
        
    # 4. Check for common keyboard mash / gibberish patterns
    gibberish_patterns = [
        r'^(asdf|qwer|zxcv|1234|hjkl|abcd)+$',
        r'^[bcdfghjklmnpqrstvwxyz]{6,}$',  # 6+ consonants with zero vowels
        r'^[0-9\W_]{6,}$'  # only numbers or symbols, no actual words
    ]
    norm_text = re.sub(r'\s+', '', clean_desc.lower())
    for pat in gibberish_patterns:
        if re.search(pat, norm_text):
            return True, "Gibberish or automated keyboard mash detected"
            
    # 5. Rate-burst check: Submissions within BURST_THRESHOLD_SECONDS (15s)
    if user and not (current_app and current_app.config.get('TESTING')):
        latest_ticket = Ticket.query.filter(
            (Ticket.reporter_id == user.id) | (Ticket.reporter_email == user.email.lower())
        ).order_by(Ticket.created_at.desc()).first()
        
        if latest_ticket and latest_ticket.created_at:
            delta = (datetime.utcnow() - latest_ticket.created_at).total_seconds()
            if delta < BURST_THRESHOLD_SECONDS:
                return True, f"Rapid-fire burst detected (submitted another ticket {int(delta)}s ago)"
                
    # 6. Duplicate Active Ticket check:
    # Exact same room + issue_type + description within DUPLICATE_WINDOW_HOURS
    if user and room_id:
        window_start = datetime.utcnow() - timedelta(hours=DUPLICATE_WINDOW_HOURS)
        duplicate = Ticket.query.filter(
            Ticket.room_id == room_id,
            Ticket.issue_type == issue_type,
            Ticket.description == clean_desc,
            (Ticket.reporter_id == user.id) | (Ticket.reporter_email == user.email.lower()),
            Ticket.created_at >= window_start
        ).first()
        
        if duplicate:
            return True, f"Duplicate ticket #{duplicate.id} already submitted for this room within the last {DUPLICATE_WINDOW_HOURS} hours"
            
    return False, ""


def apply_spam_strike_to_user(user, room_id, reason):
    """
    Applies a violation strike to the user for spamming reports.
    If active 30-day strikes reach 3, automatically suspends ad-hoc booking privileges for 14 days.
    Returns: (total_strikes_30d: int, is_suspended: bool)
    """
    if not user:
        return 0, False
        
    try:
        strike = NoShowStrike(
            faculty_id=user.id,
            room_id=room_id,
            strike_reason=f"Spam Maintenance Report: {reason}"
        )
        db.session.add(strike)
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_strikes = NoShowStrike.query.filter(
            NoShowStrike.faculty_id == user.id,
            NoShowStrike.created_at >= thirty_days_ago
        ).count() + 1
        
        is_suspended = False
        if active_strikes >= 3:
            user.adhoc_suspended_until = datetime.utcnow() + timedelta(days=14)
            is_suspended = True
            
        db.session.commit()
        return active_strikes, is_suspended
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record spam strike: {str(e)}")
        return 1, False
