"""
SLA Escalation Service (The Anti-Stagnation Protocol)
Monitors pending faculty schedule submissions. Triggers SLA breaches for batches >48h pending,
notifies Department Heads via email, and provides Super Admin override bulk-approvals.
"""
from datetime import datetime, timedelta
import logging
from . import db
from .models import ScheduleSubmission, Timetable, Room, User
from .utils import send_sla_escalation_email
from .realtime import emit_room_status_change

logger = logging.getLogger(__name__)

SLA_THRESHOLD_HOURS = 48

DEPARTMENT_HEAD_DIRECTORY = {
    "Department of Computer Science & Engineering": {
        "name": "Dr. CSE Department Head",
        "email": "cse.hod@mitwpu.edu.in"
    },
    "Department of Computer Applications (BCA/MCA)": {
        "name": "Dr. BCA/MCA Department Head",
        "email": "ca.hod@mitwpu.edu.in"
    },
    "Department of Science & Data Tech": {
        "name": "Dr. Science Tech Head",
        "email": "scitech.hod@mitwpu.edu.in"
    },
    "Department of Mechanical & Civil Engineering": {
        "name": "Dr. Core Engineering Head",
        "email": "core.hod@mitwpu.edu.in"
    }
}

DEFAULT_HEAD = {
    "name": "Department Academic Head",
    "email": "hod.academics@mitwpu.edu.in"
}


def classify_department(submission):
    """Classifies a schedule submission into its respective academic department."""
    slots = submission.schedule_data if isinstance(submission.schedule_data, list) else []
    courses = [s.get('course', '') for s in slots if s.get('course')]
    
    if any('BCA' in str(c) or 'MCA' in str(c) for c in courses):
        return "Department of Computer Applications (BCA/MCA)"
    elif any('BSc' in str(c) or 'MSc' in str(c) or 'Data' in str(c) for c in courses):
        return "Department of Science & Data Tech"
    elif any('Civil' in str(c) or 'Mech' in str(c) or 'Robotics' in str(c) for c in courses):
        return "Department of Mechanical & Civil Engineering"
    else:
        return "Department of Computer Science & Engineering"


def get_pending_batches_sla_status():
    """
    Evaluates all pending submissions against the 48-hour anti-stagnation SLA.
    Returns:
        dict: {
            'has_stale_batches': bool,
            'stale_batches_count': int,
            'total_stale_submissions': int,
            'total_stale_hours': int,
            'batches': list of batch dicts
        }
    """
    now = datetime.utcnow()
    pending_submissions = ScheduleSubmission.query.filter_by(
        status=ScheduleSubmission.STATUS_PENDING
    ).order_by(ScheduleSubmission.submitted_at.asc()).all()
    
    dept_groups = {}
    for sub in pending_submissions:
        dept = classify_department(sub)
        if dept not in dept_groups:
            dept_groups[dept] = []
        dept_groups[dept].append(sub)
        
    batches = []
    stale_batches_count = 0
    total_stale_submissions = 0
    total_stale_hours = 0
    
    for dept_name, subs in dept_groups.items():
        total_hours = sum(s.total_hours for s in subs)
        # Find oldest submission timestamp
        oldest_ts = min(
            (s.submitted_at or s.created_at or now) for s in subs
        )
        elapsed_seconds = (now - oldest_ts).total_seconds()
        elapsed_hours = round(elapsed_seconds / 3600.0, 1)
        
        is_stale = elapsed_hours >= SLA_THRESHOLD_HOURS
        hours_overdue = round(max(0.0, elapsed_hours - SLA_THRESHOLD_HOURS), 1)
        
        head_info = DEPARTMENT_HEAD_DIRECTORY.get(dept_name, DEFAULT_HEAD)
        
        if is_stale:
            stale_batches_count += 1
            total_stale_submissions += len(subs)
            total_stale_hours += total_hours
            
        batches.append({
            'department_name': dept_name,
            'submissions': subs,
            'submission_ids': [s.id for s in subs],
            'submission_count': len(subs),
            'total_hours': total_hours,
            'oldest_submitted_at': oldest_ts,
            'elapsed_hours': elapsed_hours,
            'is_stale': is_stale,
            'hours_overdue': hours_overdue,
            'sla_threshold_hours': SLA_THRESHOLD_HOURS,
            'head_name': head_info['name'],
            'head_email': head_info['email'],
            'faculty_names': [s.faculty.name if s.faculty else 'Faculty' for s in subs]
        })
        
    # Sort batches: stale first, then by elapsed hours descending
    batches.sort(key=lambda b: (not b['is_stale'], -b['elapsed_hours']))
    
    return {
        'has_stale_batches': stale_batches_count > 0,
        'stale_batches_count': stale_batches_count,
        'total_stale_submissions': total_stale_submissions,
        'total_stale_hours': total_stale_hours,
        'batches': batches
    }


def trigger_department_sla_escalation(department_name, target_email=None, admin_user=None):
    """
    Sends an immediate automated SLA escalation email ping to the Department Head / Admin.
    """
    status_data = get_pending_batches_sla_status()
    batch = next((b for b in status_data['batches'] if b['department_name'] == department_name), None)
    
    if not batch:
        return {
            'success': False,
            'message': f"No pending submissions found for {department_name}."
        }
        
    recipient_email = target_email or batch['head_email']
    recipient_name = batch['head_name']
    
    email_sent = send_sla_escalation_email(
        dept_name=department_name,
        stale_submissions_count=batch['submission_count'],
        total_hours=batch['total_hours'],
        recipient_email=recipient_email,
        recipient_name=recipient_name
    )
    
    logger.info(f"SLA Escalation ping triggered for {department_name} ({recipient_email}). Success={email_sent}")
    
    return {
        'success': True,
        'email_sent': email_sent,
        'recipient_email': recipient_email,
        'recipient_name': recipient_name,
        'stale_count': batch['submission_count'],
        'total_hours': batch['total_hours'],
        'elapsed_hours': batch['elapsed_hours'],
        'message': f"SLA escalation alert dispatched to {recipient_name} ({recipient_email})."
    }


def superadmin_override_bulk_approve(department_name, superadmin_id=None):
    """
    Super Admin override pipeline: Instantly bulk-approves all pending submissions for a department,
    clears old timetable slots, commits approved slots to live Timetable, and updates SVG map clients.
    """
    status_data = get_pending_batches_sla_status()
    batch = next((b for b in status_data['batches'] if b['department_name'] == department_name), None)
    
    if not batch or not batch['submissions']:
        return {
            'success': False,
            'message': f"No pending schedule submissions to approve in {department_name}."
        }
        
    now = datetime.utcnow()
    affected_room_ids = set()
    total_slots_created = 0
    faculty_names = []
    
    try:
        for sub in batch['submissions']:
            faculty_id = sub.faculty_id
            faculty_names.append(sub.faculty.name if sub.faculty else f"Faculty #{faculty_id}")
            
            # Wipe existing timetable records for this faculty
            Timetable.query.filter_by(faculty_id=faculty_id).delete()
            
            # Parse submission schedule slots
            slots = sub.schedule_data if isinstance(sub.schedule_data, list) else []
            for slot in slots:
                day_name = slot.get('day_name')
                day_of_week = slot.get('day_of_week')
                if day_of_week is None:
                    day_index_map = {
                        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
                    }
                    day_of_week = day_index_map.get(day_name, 0)
                    
                room_id = slot.get('room_id')
                room_number = slot.get('room_number')
                if not room_id and room_number:
                    room_obj = Room.query.filter(Room.number.ilike(room_number.strip())).first()
                    if room_obj:
                        room_id = room_obj.id
                        
                start_str = slot.get('start_time')
                time_slot_str = slot.get('time_slot')
                if not start_str and time_slot_str and '-' in time_slot_str:
                    start_str = time_slot_str.split('-')[0].strip()
                    
                duration = int(slot.get('duration', 1))
                subject = slot.get('subject', 'Assigned Lecture')
                course = slot.get('course')
                division = slot.get('division')
                
                if not (room_id and start_str):
                    continue
                    
                start_dt = datetime.strptime(start_str, '%H:%M')
                start_t = start_dt.time()
                end_t = (start_dt + timedelta(hours=duration)).time()
                
                new_tt = Timetable(
                    faculty_id=faculty_id,
                    room_id=room_id,
                    day_of_week=day_of_week,
                    start_time=start_t,
                    end_time=end_t,
                    subject=subject,
                    course=course,
                    division=division
                )
                db.session.add(new_tt)
                affected_room_ids.add(room_id)
                total_slots_created += 1
                
            sub.status = ScheduleSubmission.STATUS_APPROVED
            sub.reviewed_at = now
            sub.reviewed_by_id = superadmin_id
            sub.admin_notes = f"Super Admin Override Bulk Approval on {now.strftime('%Y-%m-%d %H:%M:%S UTC')} (Anti-Stagnation Resolution)"
            
        db.session.commit()
        
        # Real-time WebSocket sync to live SVG map
        for rid in affected_room_ids:
            try:
                r = db.session.get(Room, rid)
                if r:
                    emit_room_status_change(r, r.current_occupancy_status)
            except Exception as emit_err:
                logger.warning(f"Failed to emit room update for room {rid}: {emit_err}")
                
        return {
            'success': True,
            'approved_count': len(batch['submissions']),
            'total_slots': total_slots_created,
            'faculty_approved': faculty_names,
            'message': f"Super Admin successfully approved {len(batch['submissions'])} submissions ({total_slots_created} slots) for {department_name}."
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during super admin override bulk approve: {e}")
        return {
            'success': False,
            'message': f"Override bulk approval failed: {str(e)}"
        }
