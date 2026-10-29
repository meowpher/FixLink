"""
Email and Web Push Notification Service for FixLink.
Provides transactional email delivery via EmailJS and VAPID Web Push notifications.
"""
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# EmailJS Configuration
EMAILJS_SERVICE_ID = os.environ.get('EMAILJS_SERVICE_ID')
EMAILJS_TEMPLATE_ID = os.environ.get('EMAILJS_TEMPLATE_ID')
EMAILJS_PUBLIC_KEY = os.environ.get('EMAILJS_PUBLIC_KEY')
EMAILJS_PRIVATE_KEY = os.environ.get('EMAILJS_PRIVATE_KEY')
EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def send_ticket_email(ticket, action='created'):
    """Sends an automated email notification using EmailJS REST API."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        logger.warning(f"EmailJS is not fully configured. Skipping email for Ticket #{ticket.id} ({action}).")
        return False

    subject = f"FixLink Ticket #{ticket.id} "
    room_num = ticket.room.number if ticket.room else 'Unknown'
    if action == 'created':
        subject += "Received"
        message = f"Hello {ticket.reporter_name},\n\nYour maintenance request for room {room_num} regarding {ticket.issue_type} has been received. We will look into it shortly."
    elif action == 'in-progress':
        subject += "is In-Progress"
        message = f"Hello {ticket.reporter_name},\n\nYour maintenance request for room {room_num} is now being worked on by our team."
    elif action == 'fixed':
        subject += "is Fixed!"
        message = f"Hello {ticket.reporter_name},\n\nGood news! Your maintenance request for room {room_num} has been resolved. Thank you for using FixLink!"
    else:
        subject += "Update"
        message = f"Hello {ticket.reporter_name},\n\nThere is an update on your ticket #{ticket.id}. Its current status is: {ticket.status}."

    payload = {
        'service_id': EMAILJS_SERVICE_ID,
        'template_id': EMAILJS_TEMPLATE_ID,
        'user_id': EMAILJS_PUBLIC_KEY,
        'accessToken': EMAILJS_PRIVATE_KEY,
        'template_params': {
            'to_email': ticket.reporter_email,
            'to_name': ticket.reporter_name,
            'ticket_id': str(ticket.id),
            'subject': subject,
            'message': message,
        }
    }

    try:
        response = requests.post(
            EMAILJS_API_URL, 
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Exception while sending email for Ticket #{ticket.id}: {e}")
        return False


def send_verification_email(email, name, verification_link):
    """Send an email verification link to a newly registered user using EmailJS."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        logger.warning(f"EmailJS is not fully configured. Skipping verification email for {email}.")
        return False

    message = f"""
    Hello {name},
    
    Please verify your email address and set your password by clicking the link below:
    
    {verification_link}
    
    If you did not request this, please ignore this email.
    
    Regards,
    MIT-WPU Smart-Room Maintenance Team
    """

    payload = {
        'service_id': EMAILJS_SERVICE_ID,
        'template_id': EMAILJS_TEMPLATE_ID,
        'user_id': EMAILJS_PUBLIC_KEY,
        'accessToken': EMAILJS_PRIVATE_KEY,
        'template_params': {
            'to_email': email,
            'to_name': name,
            'subject': 'Verify Your MIT-WPU FixLink Account',
            'message': message,
            'ticket_id': '-'
        }
    }

    try:
        response = requests.post(EMAILJS_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Exception while sending verification email to {email}: {e}")
        return False


def send_password_reset_email(email, name, reset_link):
    """Send a password-reset link to a user using EmailJS."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        logger.warning(f"EmailJS is not fully configured. Skipping password reset email for {email}.")
        return False

    message = f"""
    Hello {name},
    
    We received a request to reset your FixLink account password. 
    Click the link below to set a new password:
    
    {reset_link}
    
    This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
    
    Regards,
    MIT-WPU Smart-Room Maintenance Team
    """

    payload = {
        'service_id': EMAILJS_SERVICE_ID,
        'template_id': EMAILJS_TEMPLATE_ID,
        'user_id': EMAILJS_PUBLIC_KEY,
        'accessToken': EMAILJS_PRIVATE_KEY,
        'template_params': {
            'to_email': email,
            'to_name': name,
            'subject': 'Reset Your FixLink Password',
            'message': message,
            'ticket_id': '-'
        }
    }

    try:
        response = requests.post(EMAILJS_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Exception while sending password reset email to {email}: {e}")
        return False


def send_sla_escalation_email(sla_breaches):
    """Send an automated alert notification email to facilities management."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        logger.warning("EmailJS is not fully configured. Skipping SLA escalation alert.")
        return False

    if not sla_breaches:
        return True

    recipient_email = os.environ.get('FACILITIES_HEAD_EMAIL', 'taha.piplodwala@mitwpu.edu.in')
    subject = f"URGENT: FixLink Automated SLA Escalation - {len(sla_breaches)} Department Breach(es)"
    
    lines = ["Hello Facilities Administration,\n\nThe following maintenance ticket batches have breached their SLA thresholds:\n"]
    for b in sla_breaches:
        lines.append(f"• {b['department']} Department ({b['ticket_count']} open tickets, longest pending: {b['longest_pending_hours']:.1f} hrs) -> Escalated to Level {b['escalation_level']}")
    lines.append("\nPlease review and take immediate action on the Developer/Admin Dashboard.\n\nAutomated Alert - MIT-WPU FixLink System")
    message = "\n".join(lines)

    payload = {
        'service_id': EMAILJS_SERVICE_ID,
        'template_id': EMAILJS_TEMPLATE_ID,
        'user_id': EMAILJS_PUBLIC_KEY,
        'accessToken': EMAILJS_PRIVATE_KEY,
        'template_params': {
            'to_email': recipient_email,
            'to_name': "Facilities Management",
            'subject': subject,
            'message': message,
            'ticket_id': 'SLA-ESCALATE'
        }
    }

    try:
        response = requests.post(EMAILJS_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to dispatch SLA escalation email: {e}")
        return False


def send_web_push(user_id=None, professional_id=None, title="FixLink Alert", body="", url="/"):
    """Send a Web Push notification using pywebpush with VAPID keys."""
    vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY')
    vapid_claim_email = os.environ.get('VAPID_CLAIM_EMAIL', 'admin@mitwpu.edu.in')
    if not vapid_private_key:
        return False

    from app.models import PushSubscription
    from app import db

    query = PushSubscription.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    elif professional_id is not None:
        query = query.filter_by(professional_id=professional_id)
    else:
        return False

    subs = query.all()
    if not subs:
        return False

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url,
        'icon': '/static/images/FLOGOCLR.png',
        'badge': '/static/images/logo-dm.png'
    })

    success_count = 0
    try:
        from pywebpush import webpush, WebPushException
        for sub in subs:
            try:
                sub_info = {
                    'endpoint': sub.endpoint,
                    'keys': {
                        'p256dh': sub.p256dh,
                        'auth': sub.auth
                    }
                }
                webpush(
                    subscription_info=sub_info,
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": f"mailto:{vapid_claim_email}"}
                )
                success_count += 1
            except WebPushException as ex:
                if ex.response is not None and ex.response.status_code in (404, 410):
                    db.session.delete(sub)
            except Exception:
                pass
        db.session.commit()
    except ImportError:
        logger.warning("pywebpush not installed. Web Push notifications skipped.")
        return False
    return success_count > 0

