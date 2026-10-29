"""
Admin Routes Blueprint - Maintenance Dashboard
"""
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, abort, current_app
from sqlalchemy import or_, func, case
from ... import db
from ...models import Building, Floor, Room, Asset, Ticket, User, Professional, HelpRequest, Timetable, Notification, ScheduleSubmission, AuditLog
from ...utils import send_ticket_email, allowed_file, save_webapp_file
from ...decorators import admin_required
from ...analytics import get_technician_efficiency, get_system_trends, get_critical_assets
from ...api_utils import handle_api_errors, api_response
from ...realtime import emit_room_status_change

admin_bp = Blueprint('admin', __name__)


def map_issue_to_category(issue_type, description=""):
    """Map issue_type and description to Professional category."""
    text = f"{issue_type} {description}".lower()
    
    if any(k in text for k in ['electric', 'light', 'bulb', 'switch', 'power', 'fan', 'ac', 'air_conditioner', 'plug', 'socket', 'short', 'wiring', 'wire', 'tube', 'lift']):
        return Professional.CATEGORY_ELECTRICIAN
        
    if any(k in text for k in ['plumb', 'water', 'leak', 'pipe', 'tap', 'sink', 'flush', 'drain', 'toilet', 'washroom', 'faucet']):
        return Professional.CATEGORY_PLUMBER
        
    if any(k in text for k in ['furniture', 'carpenter', 'carpentry', 'door', 'window', 'chair', 'table', 'desk', 'lock', 'bench', 'wood', 'handle']):
        return Professional.CATEGORY_CARPENTER
        
    if any(k in text for k in ['projector', 'computer', 'network', 'wifi', 'internet', 'pc', 'monitor', 'screen', 'display', 'speaker', 'mic', 'audio', 'video', 'lan', 'it']):
        return Professional.CATEGORY_IT
        
    return None


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard - view tickets and statistics."""
    from sqlalchemy import func
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    floor_filter = request.args.get('floor', 'all')
    category_filter = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query with eager loading to prevent N+1 query overhead
    from sqlalchemy.orm import joinedload
    query = Ticket.query.options(
        joinedload(Ticket.room).joinedload(Room.floor),
        joinedload(Ticket.assigned_professional),
        joinedload(Ticket.asset),
        joinedload(Ticket.reporter)
    )
    
    if status_filter != 'all':
        if status_filter == 'open':
            query = query.filter(Ticket.status == Ticket.STATUS_OPEN)
        elif status_filter == 'cancelled':
            query = query.filter(Ticket.status == Ticket.STATUS_CANCELLED)
        else:
            query = query.filter(Ticket.status == status_filter)
    
    if floor_filter != 'all':
        query = query.join(Room).filter(Room.floor_id == int(floor_filter))
        
    if category_filter != 'all':
        # Map frontend category groups to specific issue types
        if category_filter == 'electrician':
            query = query.filter(Ticket.issue_type.in_(['electrical', 'ac', 'lighting', 'lift_breakdown', 'light_broken']))
        elif category_filter == 'plumber':
            query = query.filter(Ticket.issue_type == 'plumbing')
        elif category_filter == 'it_technician':
            query = query.filter(Ticket.issue_type.in_(['projector', 'computer']))
        elif category_filter == 'carpenter':
            query = query.filter(Ticket.issue_type.in_(['furniture', 'door_error']))
        elif category_filter == 'other':
            query = query.filter(Ticket.issue_type.in_(['cleaning', 'other']))
    
    # Helper to apply floor and category filters
    def apply_dashboard_filters(q):
        if floor_filter != 'all':
            q = q.join(Room).filter(Room.floor_id == int(floor_filter))
        if category_filter != 'all':
            if category_filter == 'electrician':
                q = q.filter(Ticket.issue_type.in_(['electrical', 'ac', 'lighting', 'lift_breakdown', 'light_broken']))
            elif category_filter == 'plumber':
                q = q.filter(Ticket.issue_type == 'plumbing')
            elif category_filter == 'it_technician':
                q = q.filter(Ticket.issue_type.in_(['projector', 'computer']))
            elif category_filter == 'carpenter':
                q = q.filter(Ticket.issue_type.in_(['furniture', 'door_error']))
            elif category_filter == 'other':
                q = q.filter(Ticket.issue_type.in_(['cleaning', 'other']))
        return q

    # Paginate filtered tickets list
    pagination = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tickets = pagination.items
    
    # Statistics — single grouped query instead of 6 separate COUNT queries
    status_counts = dict(
        db.session.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )
    real_open = status_counts.get(Ticket.STATUS_OPEN, 0)
    real_cancelled = status_counts.get(Ticket.STATUS_CANCELLED, 0)
    
    # Today's tickets
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_tickets = Ticket.query.filter(Ticket.created_at >= today).count()
    
    stats = {
        'total': sum(status_counts.values()),
        'open': real_open + real_cancelled,  # Unified metric
        'assigned': status_counts.get(Ticket.STATUS_ASSIGNED, 0),
        'in_progress': status_counts.get(Ticket.STATUS_IN_PROGRESS, 0),
        'fixed': status_counts.get(Ticket.STATUS_FIXED, 0),
        'cancelled': real_cancelled,
        'today': today_tickets
    }
    
    # Get Vyas building floors for filter
    vyas = Building.query.filter_by(name='Vyas').first()
    floors = []
    if vyas:
        floors = Floor.query.filter_by(building_id=vyas.id).order_by(Floor.level).all()
    
    # Unified categories for the filter dropdown
    categories = [
        {'id': 'electrician', 'name': 'Electrical / AC / Lifts'},
        {'id': 'plumber', 'name': 'Plumbing'},
        {'id': 'it_technician', 'name': 'IT / Computer / AV'},
        {'id': 'carpenter', 'name': 'Furniture / Doors'},
        {'id': 'other', 'name': 'Others'}
    ]
    
    # Filtered queries for the status boxes on the dashboard
    from sqlalchemy.orm import joinedload
    
    base_box_query = Ticket.query.options(joinedload(Ticket.room), joinedload(Ticket.assigned_professional))
    base_box_query = apply_dashboard_filters(base_box_query)

    if status_filter == 'all':
        open_tickets = base_box_query.filter(
            Ticket.status.in_([Ticket.STATUS_OPEN, Ticket.STATUS_CANCELLED])
        ).order_by(Ticket.created_at.desc()).all()
        assigned_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_ASSIGNED).order_by(Ticket.created_at.desc()).all()
        in_progress_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_IN_PROGRESS).order_by(Ticket.created_at.desc()).all()
        fixed_tickets = []
    elif status_filter == 'open':
        open_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_OPEN).order_by(Ticket.created_at.desc()).all()
        assigned_tickets = []
        in_progress_tickets = []
        fixed_tickets = []
    elif status_filter == 'cancelled':
        open_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_CANCELLED).order_by(Ticket.created_at.desc()).all()
        assigned_tickets = []
        in_progress_tickets = []
        fixed_tickets = []
    elif status_filter == 'assigned':
        open_tickets = []
        assigned_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_ASSIGNED).order_by(Ticket.created_at.desc()).all()
        in_progress_tickets = []
        fixed_tickets = []
    elif status_filter == 'in-progress':
        open_tickets = []
        assigned_tickets = []
        in_progress_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_IN_PROGRESS).order_by(Ticket.created_at.desc()).all()
        fixed_tickets = []
    elif status_filter == 'fixed':
        open_tickets = []
        assigned_tickets = []
        in_progress_tickets = []
        fixed_tickets = base_box_query.filter(Ticket.status == Ticket.STATUS_FIXED).order_by(Ticket.created_at.desc()).all()
    else:
        open_tickets = []
        assigned_tickets = []
        in_progress_tickets = []
        fixed_tickets = []

    return render_template('admin.html',
                         tickets=tickets,
                         open_tickets=open_tickets,
                         assigned_tickets=assigned_tickets,
                         in_progress_tickets=in_progress_tickets,
                         fixed_tickets=fixed_tickets,
                         pagination=pagination,
                         stats=stats,
                         floors=floors,
                         categories=categories,
                         status_filter=status_filter,
                         floor_filter=floor_filter,
                         category_filter=category_filter)


def _get_faculty_handle_context():
    """Build unified dataset required by the Faculty Admin Handle console."""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    from ...models import Timetable, Floor, Room, User, Building, NoShowStrike, SuspensionLog, EventBooking
    from datetime import date, datetime, timedelta, timezone

    # 1. Event Approvals Data
    pending_events = EventBooking.query.filter_by(status='Pending').order_by(EventBooking.start_date.asc()).all()
    upcoming_events = EventBooking.query.filter(
        EventBooking.status == 'Approved',
        EventBooking.end_date >= date.today()
    ).order_by(EventBooking.start_date.asc()).all()
    history_events = EventBooking.query.filter(
        (EventBooking.status.in_(['Rejected', 'Cancelled'])) | 
        ((EventBooking.status == 'Approved') & (EventBooking.end_date < date.today()))
    ).order_by(EventBooking.created_at.desc()).limit(50).all()

    # 2. CMM Data
    unassigned_classes = Timetable.query.options(joinedload(Timetable.room)).filter(
        Timetable.faculty_id.is_(None)
    ).order_by(Timetable.day_of_week, Timetable.start_time).all()

    all_faculties = User.query.filter_by(role=User.ROLE_FACULTY, is_active=True).order_by(User.name).all()

    vyas = Building.query.filter_by(name='Vyas').first()
    if vyas:
        floors = Floor.query.options(joinedload(Floor.rooms)).filter_by(building_id=vyas.id).order_by(Floor.level).all()
        rooms = Room.query.join(Floor).filter(Floor.building_id == vyas.id).order_by(Room.number).all()
    else:
        floors = Floor.query.options(joinedload(Floor.rooms)).order_by(Floor.level).all()
        rooms = Room.query.order_by(Room.number).all()

    academic_floors = []
    for f in floors:
        floor_rooms = []
        for r in sorted(f.rooms, key=lambda x: x.number or ''):
            num = (r.number or '').strip()
            name = (r.name or '').strip().lower()
            rtype = (r.room_type or '').strip().lower()
            
            # Exclude Lifts
            if 'lift' in num.lower() or 'lift' in name or rtype == 'lift':
                continue
            # Exclude Washrooms
            if 'washroom' in name or rtype == 'washroom':
                continue
            # Exclude MR (Meeting Rooms)
            if num.upper().startswith('MR') or rtype == 'meeting_room' or 'meeting room' in name:
                continue
            # Exclude ENCAVE
            if num.upper() == 'ENCAVE' or 'encave' in name or rtype == 'canteen' or 'canteen' in name:
                continue
                
            floor_rooms.append(r)
        if floor_rooms:
            academic_floors.append({
                'floor': f,
                'name': f.name,
                'level': f.level,
                'rooms': floor_rooms
            })

    total_timetables_count = Timetable.query.count()
    assigned_count = Timetable.query.filter(Timetable.faculty_id.isnot(None)).count()
    unassigned_count = len(unassigned_classes)

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    unassigned_classes_data = [
        {
            'id': cls.id,
            'course': cls.course or '',
            'subject': cls.subject or '',
            'division': cls.division or '',
            'room_number': cls.room.number if cls.room else (f"Room #{cls.room_id}" if cls.room_id else ""),
            'room_id': cls.room_id,
            'day_of_week': cls.day_of_week,
            'day_name': day_names[cls.day_of_week] if (cls.day_of_week is not None and 0 <= cls.day_of_week < 7) else (f"Day {cls.day_of_week}" if cls.day_of_week is not None else ""),
            'start_time': cls.start_time.strftime('%I:%M %p') if cls.start_time else '',
            'end_time': cls.end_time.strftime('%I:%M %p') if cls.end_time else '',
        }
        for cls in unassigned_classes
    ]
    all_faculties_data = [{'id': fac.id, 'name': fac.name} for fac in all_faculties]

    # 3. Ghost Protocol Data
    IST = timezone(timedelta(hours=5, minutes=30))
    now_utc = datetime.utcnow()
    cutoff_30d = now_utc - timedelta(days=30)

    strike_counts = (
        db.session.query(
            NoShowStrike.faculty_id,
            func.count(NoShowStrike.id).label('total_strikes'),
            func.max(NoShowStrike.created_at).label('last_strike_at')
        )
        .filter(NoShowStrike.created_at >= cutoff_30d)
        .group_by(NoShowStrike.faculty_id)
        .order_by(func.count(NoShowStrike.id).desc())
        .all()
    )

    flagged_faculty = []
    seen_ids = set()
    for row in strike_counts:
        user = db.session.get(User, row.faculty_id)
        if not user:
            continue
        seen_ids.add(user.id)
        all_time = NoShowStrike.query.filter_by(faculty_id=row.faculty_id).count()
        recent_strikes = NoShowStrike.query.filter(
            NoShowStrike.faculty_id == row.faculty_id,
            NoShowStrike.created_at >= cutoff_30d
        ).order_by(NoShowStrike.created_at.desc()).all()

        suspended = user.adhoc_suspended_until and user.adhoc_suspended_until > now_utc
        suspended_until_ist = None
        if user.adhoc_suspended_until:
            dt = user.adhoc_suspended_until
            suspended_until_ist = dt.replace(tzinfo=timezone.utc).astimezone(IST) if dt.tzinfo is None else dt.astimezone(IST)

        flagged_faculty.append({
            'user': user,
            'strikes_30d': row.total_strikes,
            'all_time_strikes': all_time,
            'last_strike_at': row.last_strike_at,
            'is_suspended': suspended,
            'suspended_until': suspended_until_ist,
            'suspension_reason': getattr(user, 'adhoc_suspension_reason', None),
            'recent_strikes': recent_strikes
        })

    suspended_extra = User.query.filter(
        User.adhoc_suspended_until > now_utc,
        User.role == User.ROLE_FACULTY
    ).all()
    for user in suspended_extra:
        if user.id not in seen_ids:
            all_time = NoShowStrike.query.filter_by(faculty_id=user.id).count()
            dt = user.adhoc_suspended_until
            suspended_until_ist = dt.replace(tzinfo=timezone.utc).astimezone(IST) if dt.tzinfo is None else dt.astimezone(IST)
            flagged_faculty.append({
                'user': user,
                'strikes_30d': 0,
                'all_time_strikes': all_time,
                'last_strike_at': None,
                'is_suspended': True,
                'suspended_until': suspended_until_ist,
                'suspension_reason': getattr(user, 'adhoc_suspension_reason', None),
                'recent_strikes': []
            })

    total_strikes_ever = NoShowStrike.query.count()
    strikes_30d_total = NoShowStrike.query.filter(NoShowStrike.created_at >= cutoff_30d).count()
    currently_suspended_count = User.query.filter(
        User.adhoc_suspended_until > now_utc,
        User.role == User.ROLE_FACULTY
    ).count()
    red_flag_count = len([f for f in flagged_faculty if f['strikes_30d'] >= 3])

    suspension_history = (
        SuspensionLog.query
        .options(joinedload(SuspensionLog.faculty), joinedload(SuspensionLog.lifted_by))
        .order_by(SuspensionLog.created_at.desc())
        .limit(200)
        .all()
    )
    history_display = []
    for entry in suspension_history:
        created_ist = entry.created_at.replace(tzinfo=timezone.utc).astimezone(IST) if entry.created_at.tzinfo is None else entry.created_at.astimezone(IST)
        until_ist = None
        if entry.suspended_until:
            until_ist = entry.suspended_until.replace(tzinfo=timezone.utc).astimezone(IST) if entry.suspended_until.tzinfo is None else entry.suspended_until.astimezone(IST)
        history_display.append({
            'entry': entry,
            'created_ist': created_ist,
            'suspended_until_ist': until_ist,
        })

    # 4. Room Booking History Data
    from ...models import RoomBooking
    booking_history_list = RoomBooking.query.options(
        joinedload(RoomBooking.faculty),
        joinedload(RoomBooking.room).joinedload(Room.floor)
    ).order_by(RoomBooking.slot_start.desc()).limit(150).all()
    total_bookings_count = RoomBooking.query.count()

    return {
        'pending_events': pending_events,
        'upcoming_events': upcoming_events,
        'history_events': history_events,
        'unassigned_classes_data': unassigned_classes_data,
        'all_faculties_data': all_faculties_data,
        'all_faculties': all_faculties,
        'floors': floors,
        'academic_floors': academic_floors,
        'rooms': rooms,
        'total_timetables_count': total_timetables_count,
        'assigned_count': assigned_count,
        'unassigned_count': unassigned_count,
        'flagged_faculty': flagged_faculty,
        'total_strikes_ever': total_strikes_ever,
        'strikes_30d_total': strikes_30d_total,
        'currently_suspended_count': currently_suspended_count,
        'red_flag_count': red_flag_count,
        'now_utc': now_utc,
        'suspension_history': history_display,
        'booking_history_list': booking_history_list,
        'total_bookings_count': total_bookings_count
    }


@admin_bp.route('/faculty-admin-handle')
@admin_bp.route('/faculty-handle')
@admin_required
def faculty_admin_handle():
    """Unified Faculty Admin Handle console combining Event Approvals, CMM, Ghost Protocol, and Booking History."""
    raw_tab = request.args.get('tab', 'events').strip().lower()
    if raw_tab in ['events', 'event', 'approvals']:
        active_tab = 'events'
    elif raw_tab in ['cmm', 'classroom', 'timetables', 'timetable', 'classes']:
        active_tab = 'cmm'
    elif raw_tab in ['ghost', 'ghost_protocol', 'ghost-protocol', 'strikes']:
        active_tab = 'ghost'
    elif raw_tab in ['bookings', 'booking', 'booking_history', 'booking-history', 'reservations']:
        active_tab = 'bookings'
    else:
        active_tab = 'events'

    ctx = _get_faculty_handle_context()
    return render_template('admin/faculty_handle.html', active_tab=active_tab, **ctx)


@admin_bp.route('/classroom-management')
@admin_bp.route('/cmm')
@admin_required
def classroom_management():
    """Redirect to unified Faculty Admin Handle CMM tab."""
    return redirect(url_for('admin.faculty_admin_handle', tab='cmm'))



@admin_bp.route('/map')

@admin_required
def status_map():
    """Visual status map showing all floors with room status - Optimized."""
    floor_id = request.args.get('floor', type=int)
    
    # Get Vyas building and floors
    vyas = Building.query.filter_by(name='Vyas').first()
    floors = []
    selected_floor = None
    rooms = []
    
    if vyas:
        floors = Floor.query.filter(Floor.building_id == vyas.id).order_by(Floor.level).all()
        
        if floor_id:
            selected_floor = db.session.get(Floor, floor_id)
        elif floors:
            selected_floor = floors[0]
        
        if selected_floor:
            from sqlalchemy.orm import joinedload
            from ...models import RoomBooking, Timetable, EventBooking
            rooms = Room.query.options(
                joinedload(Room.tickets),
                joinedload(Room.assets),
                joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
                joinedload(Room.timetables).joinedload(Timetable.faculty),
                joinedload(Room.booked_events).joinedload(EventBooking.faculty)
            ).filter_by(floor_id=selected_floor.id).all()
            
    rooms_data = [room.to_map_dict() for room in rooms] if rooms else []
    
    return render_template('status_map.html',
                         floors=floors,
                         selected_floor=selected_floor,
                         rooms=rooms,
                         rooms_data=rooms_data)


@admin_bp.route('/history')
@admin_required
def history():
    """Admin history page - view fixed tickets with search filtering."""
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Base query for all fixed tickets
    from sqlalchemy.orm import joinedload
    query = Ticket.query.options(joinedload(Ticket.room).joinedload(Room.floor)).filter_by(status=Ticket.STATUS_FIXED)
    
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            or_(
                Ticket.reporter_name.ilike(search_filter),
                Ticket.prn.ilike(search_filter),
                Ticket.reporter_email.ilike(search_filter)
            )
        )
    
    # Order by fixed date descending and paginate
    pagination = query.order_by(Ticket.fixed_at.desc(), Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    tickets = pagination.items
    
    return render_template('admin_history.html', 
                          tickets=tickets, 
                          pagination=pagination,
                          search_query=search_query)

@admin_bp.route('/booking-history')
@admin_required
def booking_history():
    """Admin view for faculty classroom bookings."""
    from ...models import RoomBooking
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_query = request.args.get('search', '').strip()
    from sqlalchemy.orm import joinedload
    query = RoomBooking.query.options(
        joinedload(RoomBooking.faculty),
        joinedload(RoomBooking.room).joinedload(Room.floor)
    ).join(RoomBooking.faculty).join(RoomBooking.room)
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                User.name.ilike(search),
                User.email.ilike(search),
                Room.number.ilike(search),
                RoomBooking.subject.ilike(search),
                RoomBooking.division.ilike(search),
                RoomBooking.course.ilike(search)
            )
        )
        
    query = query.order_by(RoomBooking.slot_start.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_booking_history.html', 
                          bookings=pagination.items, 
                          pagination=pagination,
                          search_query=search_query)


@admin_bp.route('/users')
@admin_required
def users():
    """User Management page."""
    search_query = request.args.get('q', '').strip()
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')
    sort_filter = request.args.get('sort', 'newest')
    designation_filter = request.args.get('designation')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = User.query.filter_by(is_active=True)

    if designation_filter:
        if designation_filter in ['Program Director', 'Associate Professor & Program Director']:
            query = query.filter(User.designation.ilike('%Program Director%'))
        elif designation_filter in ['Program Head', 'Professor & Program Head']:
            query = query.filter(User.designation.ilike('%Program Head%'))
        else:
            query = query.filter(User.designation == designation_filter)

    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                User.name.ilike(search),
                User.email.ilike(search),
                User.prn.ilike(search)
            )
        )

    if role_filter == 'admin':
        query = query.filter_by(is_admin=True)
    elif role_filter == 'reporter':
        query = query.filter_by(is_admin=False)
        
    if status_filter == 'verified':
        query = query.filter_by(is_verified=True)
    elif status_filter == 'unverified':
        query = query.filter_by(is_verified=False)
        
    if sort_filter == 'newest':
        query = query.order_by(User.created_at.desc())
    elif sort_filter == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort_filter == 'name':
        query = query.order_by(User.name.asc())
        
    total = query.count()
    users_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_users.html',
                           users=users_paginated.items,
                           total=total,
                           page=page,
                           pages=users_paginated.pages,
                           per_page=per_page,
                           search_query=search_query,
                           role_filter=role_filter,
                           status_filter=status_filter,
                           designation_filter=designation_filter,
                           sort=sort_filter)


@admin_bp.route('/users/promote', methods=['POST'])
def promote_user():
    """
    Promote a Faculty user to SUPERVISOR role (Phase 2).
    Strictly verifies that the requester has SUPER_ADMIN authorization.
    Updates role to SUPERVISOR and commits immutable AuditLog record.
    """
    from ...models import AuditLog
    
    # 1. Strictly verify Super Admin privileges
    is_super_admin = session.get('is_super_admin')
    if not is_super_admin and 'user_id' in session:
        requester = db.session.get(User, session['user_id'])
        if requester and requester.is_super_admin:
            is_super_admin = True
            session['is_super_admin'] = True

    if not is_super_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Unauthorized: Super Admin privileges required.", status=403)
        flash("Unauthorized: Super Admin privileges required to assign Supervisor role.", "error")
        return redirect(url_for('superadmin.dashboard'))

    # 2. Extract target user identity (supports user_id or email)
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or request.form.get('user_id')
    email = data.get('email') or request.form.get('email')

    target_user = None
    if user_id:
        try:
            target_user = db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            pass
    if not target_user and email:
        target_user = User.query.filter(db.func.lower(User.email) == str(email).strip().lower()).first()

    if not target_user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Target user not found.", status=404)
        flash("Target user not found.", "error")
        return redirect(url_for('superadmin.dashboard'))

    # 3. Update target user's role to SUPERVISOR and grant admin privileges
    target_user.role = User.ROLE_SUPERVISOR
    target_user.is_admin = True

    # 4. Write immutable AuditLog record
    admin_id = session.get('user_id')
    admin_user = db.session.get(User, admin_id) if admin_id else None
    promoter_name = admin_user.name if admin_user else session.get('super_admin_email', 'Super Admin')

    audit_entry = AuditLog(
        action="USER_PROMOTED_TO_SUPERVISOR",
        details=f"Faculty {target_user.name} ({target_user.email}) was promoted to SUPERVISOR by Super Admin {promoter_name}.",
        user_id=admin_id,
        target_type="User",
        target_id=target_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(audit_entry)
    db.session.commit()

    success_msg = f"User {target_user.name} ({target_user.email}) successfully promoted to SUPERVISOR."
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return api_response(success=True, message=success_msg, data={
            'user': {
                'id': target_user.id,
                'name': target_user.name,
                'email': target_user.email,
                'role': target_user.role,
                'is_supervisor': target_user.is_supervisor,
                'is_admin': target_user.is_admin
            }
        })

    flash(success_msg, "success")
    return redirect(url_for('superadmin.dashboard'))


@admin_bp.route('/users/demote', methods=['POST'])
def demote_user():
    """
    Demote a SUPERVISOR user to FACULTY role (Phase 2).
    Strictly verifies that the requester has SUPER_ADMIN authorization.
    Protects Super Admin accounts from demotion.
    Updates target user role to FACULTY, sets is_admin to False,
    and writes an immutable AuditLog record in a single atomic db.session.commit().
    """
    from ...models import AuditLog

    # 1. Strictly verify Super Admin privileges
    is_super_admin = session.get('is_super_admin')
    if not is_super_admin and 'user_id' in session:
        requester = db.session.get(User, session['user_id'])
        if requester and requester.is_super_admin:
            is_super_admin = True
            session['is_super_admin'] = True

    if not is_super_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Unauthorized: Super Admin privileges required.", status=403)
        flash("Unauthorized: Super Admin privileges required to demote users.", "error")
        return redirect(url_for('superadmin.dashboard'))

    # 2. Extract target user identity (supports user_id or email)
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or request.form.get('user_id')
    email = data.get('email') or request.form.get('email')

    target_user = None
    if user_id:
        try:
            target_user = db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            pass
    if not target_user and email:
        target_user = User.query.filter(db.func.lower(User.email) == str(email).strip().lower()).first()

    if not target_user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Target user not found.", status=404)
        flash("Target user not found.", "error")
        return redirect(url_for('superadmin.dashboard'))

    # 3. Safeguard: Super Admins cannot be demoted
    if target_user.is_super_admin or (target_user.role or '').upper() == User.ROLE_SUPER_ADMIN:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return api_response(success=False, error="Security violation: Super Admin accounts cannot be demoted.", status=400)
        flash("Security violation: Super Admin accounts cannot be demoted.", "error")
        return redirect(url_for('superadmin.dashboard'))

    # 4. Update target user's role to FACULTY and revoke supervisor/admin privileges
    target_user.role = User.ROLE_FACULTY
    target_user.is_admin = False

    # 5. Write immutable AuditLog record
    admin_id = session.get('user_id')
    admin_user = db.session.get(User, admin_id) if admin_id else None
    demoter_name = admin_user.name if admin_user else session.get('super_admin_email', 'Super Admin')

    audit_entry = AuditLog(
        ticket_id=None,
        action="USER_DEMOTED_TO_FACULTY",
        performed_by_id=admin_id,
        timestamp=datetime.utcnow(),
        details=f"Supervisor {target_user.name} ({target_user.email}) was demoted to FACULTY by Super Admin {demoter_name}.",
        user_id=admin_id,
        target_type="User",
        target_id=target_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(audit_entry)
    db.session.commit()

    success_msg = f"User {target_user.name} ({target_user.email}) successfully demoted to FACULTY."
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return api_response(success=True, message=success_msg, data={
            'user': {
                'id': target_user.id,
                'name': target_user.name,
                'email': target_user.email,
                'role': target_user.role,
                'is_supervisor': target_user.is_supervisor,
                'is_admin': target_user.is_admin
            }
        })

    flash(success_msg, "success")
    return redirect(url_for('superadmin.dashboard'))


@admin_bp.route('/audit-trail', methods=['GET'])
@admin_bp.route('/audit-logs', methods=['GET'])
@admin_required
def audit_trail():
    """
    Audit Trail View (Phase 2).
    Streams immutable system audit events.
    To prevent memory crashes under load, this data table MUST be paginated using
    SQLAlchemy's .paginate(page=page, per_page=20) without loading all records into memory at once.
    """
    from ...models import AuditLog, Ticket
    from sqlalchemy.orm import joinedload

    page = request.args.get('page', 1, type=int)
    per_page = 20
    action_filter = request.args.get('action', '').strip()
    ticket_filter = request.args.get('ticket_id', type=int)

    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if ticket_filter:
        query = query.filter(
            (AuditLog.ticket_id == ticket_filter) |
            ((AuditLog.target_type == 'Ticket') & (AuditLog.target_id == ticket_filter))
        )

    # Eager load relationships to prevent N+1 queries
    query = query.options(
        joinedload(AuditLog.ticket),
        joinedload(AuditLog.performed_by),
        joinedload(AuditLog.user)
    )

    # Ensure uniqueness: For TICKET_VERIFIED_CLOSED, only show the latest verification log per ticket
    unique_verified_subquery = (
        db.session.query(func.max(AuditLog.id))
        .filter(AuditLog.action == "TICKET_VERIFIED_CLOSED")
        .group_by(func.coalesce(AuditLog.ticket_id, AuditLog.target_id))
    )
    query = query.filter(
        or_(
            AuditLog.action != "TICKET_VERIFIED_CLOSED",
            AuditLog.id.in_(unique_verified_subquery)
        )
    )

    # Strictly paginate query at the database level (LIMIT 20 OFFSET ...) to protect memory
    pagination = query.order_by(AuditLog.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    audit_logs = pagination.items

    # Pre-resolve any Ticket objects for logs where ticket_id wasn't a direct foreign key but target_id was
    needed_ticket_ids = {
        log.target_id for log in audit_logs
        if not log.ticket and log.target_type == 'Ticket' and log.target_id
    }
    additional_tickets = {}
    if needed_ticket_ids:
        additional_tickets = {t.id: t for t in Ticket.query.filter(Ticket.id.in_(needed_ticket_ids)).all()}

    for log in audit_logs:
        if not log.ticket and log.target_type == 'Ticket' and log.target_id in additional_tickets:
            log._resolved_ticket = additional_tickets[log.target_id]
        else:
            log._resolved_ticket = log.ticket

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('format') == 'json':
        return api_response(
            success=True,
            data={
                'logs': [log.to_dict() for log in audit_logs],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                }
            }
        )

    # Standard human-readable action definitions
    SYSTEM_ACTIONS = [
        ('TICKET_VERIFIED_CLOSED', 'Ticket Verified & Closed (Supervisor QA)'),
        ('USER_PROMOTED_TO_SUPERVISOR', 'User Promoted to Supervisor'),
        ('USER_DEMOTED_TO_FACULTY', 'User Demoted to Faculty'),
        ('FACULTY_EVENT_APPROVED', 'Faculty Reservation Approved'),
        ('FACULTY_EVENT_REJECTED', 'Faculty Reservation Rejected'),
        ('SUSPENSION_LIFTED', 'Ghost Protocol Suspension Lifted'),
        ('STRIKES_CLEARED', 'No-Show Strikes Reset'),
        ('TIMETABLE_IMPORTED', 'Academic Timetable Imported'),
    ]
    try:
        db_actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all() if r[0]]
    except Exception as e:
        logger.warning(f"Failed to query distinct AuditLog actions: {e}")
        db_actions = []

    action_dict = dict(SYSTEM_ACTIONS)
    for act in db_actions:
        if act not in action_dict:
            action_dict[act] = act.replace('_', ' ').title()

    distinct_actions = [(act, action_dict[act]) for act in sorted(action_dict.keys(), key=lambda k: action_dict[k])]

    return render_template(
        'admin/audit_trail.html',
        pagination=pagination,
        audit_logs=audit_logs,
        action_filter=action_filter,
        ticket_filter=ticket_filter,
        distinct_actions=distinct_actions,
        page=page,
        pages=pagination.pages,
        total=pagination.total
    )


@admin_bp.route('/tickets/<int:ticket_id>/proof', methods=['GET'])
@admin_required
def get_ticket_proof_details(ticket_id):
    """Fetch supervisor proof image and QA verification details for a ticket."""
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return api_response(success=False, message="Ticket not found", status_code=404)

    supervisor = ticket.verified_by
    proof_url = ticket.proof_of_completion_url or ticket.proof_image_url
    initial_img = f"/static/uploads/{ticket.image_filename}" if ticket.image_filename else None

    return api_response(
        success=True,
        data={
            'ticket_id': ticket.id,
            'issue_type': ticket.issue_type,
            'description': ticket.description,
            'status': ticket.status,
            'proof_url': proof_url,
            'initial_image_url': initial_img,
            'resolution_notes': ticket.resolution_notes or "Verified on-site and confirmed fully operational.",
            'resolved_at': ticket.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC') if ticket.resolved_at else (ticket.fixed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if ticket.fixed_at else None),
            'supervisor_name': supervisor.name if supervisor else (ticket.assigned_vendor_or_tech_name or 'Supervisor'),
            'supervisor_role': getattr(supervisor, 'role', 'SUPERVISOR') if supervisor else 'SUPERVISOR',
            'room_number': ticket.room.number if ticket.room else None,
            'floor_name': ticket.room.floor.name if (ticket.room and ticket.room.floor) else None
        }
    )




def generate_sparkline_svg(data_points, width=100, height=30, padding=4):
    """Generate SVG path string (d attribute) from a series of data points."""
    if not data_points or len(data_points) < 2:
        return f"M0,{height - padding} L{width},{height - padding}"
    
    max_val = max(data_points)
    min_val = min(data_points)
    val_range = max_val - min_val
    if val_range == 0:
        val_range = 1
        
    usable_h = height - (padding * 2)
    step_x = width / (len(data_points) - 1)
    
    coords = []
    for i, v in enumerate(data_points):
        x = round(i * step_x, 1)
        y = round(height - padding - ((v - min_val) / val_range * usable_h), 1)
        coords.append((x, y))
        
    path = f"M{coords[0][0]},{coords[0][1]}"
    for i in range(1, len(coords)):
        prev_x, prev_y = coords[i - 1]
        curr_x, curr_y = coords[i]
        mid_x = round((prev_x + curr_x) / 2, 1)
        path += f" C{mid_x},{prev_y} {mid_x},{curr_y} {curr_x},{curr_y}"
    return path


@admin_bp.route('/analytics')
@admin_bp.route('/api/analytics', endpoint='api_analytics')
@admin_required
def analytics():
    """Admin analytics and insights dashboard with dynamic filtering."""
    # Get filters from request
    period = request.args.get('period', 'monthly')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Base Filters
    query = Ticket.query
    
    # 1. Date Range Handling
    now = datetime.utcnow()
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Ticket.created_at.between(start_date, end_date))
            window_len = end_date - start_date
        except ValueError:
            start_date = now - timedelta(days=180)
            end_date = now
            window_len = timedelta(days=180)
    elif period == 'daily':
        # Default to last 14 days for daily
        start_date = now - timedelta(days=14)
        end_date = now
        window_len = timedelta(days=14)
        query = query.filter(Ticket.created_at >= start_date)
    elif period == 'weekly':
        # Default to last 12 weeks
        start_date = now - timedelta(weeks=12)
        end_date = now
        window_len = timedelta(weeks=12)
        query = query.filter(Ticket.created_at >= start_date)
    else: # Default monthly
        start_date = now - timedelta(days=180)
        end_date = now
        window_len = timedelta(days=180)
        query = query.filter(Ticket.created_at >= start_date)

    # 2. Total/Fixed Stats (Respecting filters)
    total_tickets = query.count()
    fixed_tickets_count = query.filter(Ticket.status == Ticket.STATUS_FIXED).count()
    
    # Prior Window Calculation for Actual Comparative Trends
    prior_end = start_date
    prior_start = start_date - window_len
    prior_query = Ticket.query.filter(Ticket.created_at >= prior_start, Ticket.created_at < prior_end)
    prior_total = prior_query.count()
    prior_fixed = prior_query.filter(Ticket.status == Ticket.STATUS_FIXED).count()
    
    prior_success_rate = round((prior_fixed / prior_total * 100), 1) if prior_total > 0 else 0
    prior_fixed_tickets = prior_query.filter(Ticket.status == Ticket.STATUS_FIXED, Ticket.job_completed_at.isnot(None)).all()
    prior_avg_time = 0
    if prior_fixed_tickets:
        p_durations = [(t.job_completed_at - t.created_at).total_seconds() for t in prior_fixed_tickets if t.job_completed_at and t.created_at]
        if p_durations:
            prior_avg_time = round(sum(p_durations) / (3600 * len(p_durations)), 1)
    
    # 3. Tickets by Category (Respecting filters)
    raw_category_counts = db.session.query(
        Ticket.issue_type, func.count(Ticket.id)
    ).filter(Ticket.created_at >= start_date).group_by(Ticket.issue_type).all()
    
    # Re-use your consolidated grouping logic
    category_map = {
        'electrical': 'Electrical & Utilities', 'ac': 'Electrical & Utilities', 
        'lighting': 'Electrical & Utilities', 'light_broken': 'Electrical & Utilities',
        'lift_breakdown': 'Electrical & Utilities', 'lift_not_working': 'Electrical & Utilities',
        'projector': 'IT & AV Systems', 'computer': 'IT & AV Systems',
        'plumbing': 'Plumbing', 'furniture': 'Furniture & Carpentry', 
        'chairs': 'Furniture & Carpentry', 'door_error': 'Furniture & Carpentry',
    }
    
    consolidated_data = {}
    for issue_type, count in raw_category_counts:
        group_name = category_map.get(issue_type, 'Other')
        consolidated_data[group_name] = consolidated_data.get(group_name, 0) + count
    
    # 4. Success Rate
    success_rate = round((fixed_tickets_count / total_tickets * 100), 1) if total_tickets > 0 else 0
    
    # 5. Average Resolution Time (Filtered)
    avg_res_time = 0
    try:
        # Fast SQL Aggregation (PostgreSQL)
        avg_res_seconds = query.filter(
            Ticket.status == Ticket.STATUS_FIXED,
            Ticket.job_completed_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', Ticket.job_completed_at) - func.extract('epoch', Ticket.created_at))
        ).scalar()
        if avg_res_seconds:
            avg_res_time = round(float(avg_res_seconds) / 3600, 1)
    except Exception:
        # Fallback for SQLite / Testing
        fixed_tickets_q = query.filter(
            Ticket.status == Ticket.STATUS_FIXED,
            Ticket.job_completed_at.isnot(None)
        ).all()
        
        if fixed_tickets_q:
            durations = [
                (t.job_completed_at - t.created_at).total_seconds() 
                for t in fixed_tickets_q 
                if t.job_completed_at and t.created_at
            ]
            if durations:
                avg_res_time = round(sum(durations) / (3600 * len(durations)), 1) # in hours

    # 6. Trend Grouping Based on Period (Works seamlessly on SQLite & PostgreSQL)
    trend_data = []
    is_sqlite = db.engine.dialect.name == 'sqlite'
    if is_sqlite:
        date_fmt = '%Y-%m-%d' if period == 'daily' else ('%Y-%W' if period == 'weekly' else '%Y-%m')
        label_expr = func.strftime(date_fmt, Ticket.created_at)
    else:
        date_fmt = 'YYYY-MM-DD' if period == 'daily' else ('IYYY-"W"IW' if period == 'weekly' else 'YYYY-MM')
        label_expr = func.to_char(Ticket.created_at, date_fmt)

    try:
        trend_query = db.session.query(
            label_expr.label('label'),
            func.count(Ticket.id)
        ).filter(Ticket.created_at >= start_date).group_by('label').order_by('label').all()
        trend_data = [list(row) for row in trend_query]
    except Exception as e:
        current_app.logger.warning(f"Trend query fallback: {e}")

    # 7. Compute Real Sparklines & Actual Trend Deltas
    vol_points = [row[1] for row in trend_data] if trend_data else []
    vol_sparkline = generate_sparkline_svg(vol_points)
    
    # Resolved time series
    try:
        res_trend_query = db.session.query(
            label_expr.label('label'),
            func.count(Ticket.id)
        ).filter(Ticket.created_at >= start_date, Ticket.status == Ticket.STATUS_FIXED).group_by('label').order_by('label').all()
        res_dict = dict(res_trend_query)
        res_points = [res_dict.get(row[0], 0) for row in trend_data]
    except Exception:
        res_points = []
    res_sparkline = generate_sparkline_svg(res_points)
    
    # Success rate points
    sr_points = []
    if trend_data and res_points:
        for i, row in enumerate(trend_data):
            tot = row[1]
            fix = res_points[i] if i < len(res_points) else 0
            sr_points.append(round((fix / tot * 100), 1) if tot > 0 else 0)
    sr_sparkline = generate_sparkline_svg(sr_points)
    
    time_sparkline = generate_sparkline_svg([avg_res_time, avg_res_time] if avg_res_time > 0 else [])

    # Real percentage changes vs prior window
    if prior_total > 0:
        vol_diff = round(((total_tickets - prior_total) / prior_total) * 100)
        vol_trend = f"{'+' if vol_diff > 0 else ''}{vol_diff}%"
    elif total_tickets > 0:
        vol_trend = "+100%"
    else:
        vol_trend = "0%"

    if prior_fixed > 0:
        res_diff = round(((fixed_tickets_count - prior_fixed) / prior_fixed) * 100)
        res_trend = f"{'+' if res_diff > 0 else ''}{res_diff}%"
    elif fixed_tickets_count > 0:
        res_trend = "+100%"
    else:
        res_trend = "0%"

    sr_diff = round(success_rate - prior_success_rate, 1)
    sr_trend = f"{'+' if sr_diff > 0 else ''}{sr_diff}%" if sr_diff != 0 else "0%"

    if avg_res_time > 0 and prior_avg_time > 0:
        time_diff = round(avg_res_time - prior_avg_time, 1)
        time_trend = f"{'+' if time_diff > 0 else ''}{time_diff}h"
    elif avg_res_time > 0:
        time_trend = f"{avg_res_time}h"
    else:
        time_trend = "0h"

    advanced_stats = [
        {
            'label': 'Total Volume',
            'value': total_tickets,
            'trend': vol_trend,
            'desc': 'Tickets in selected window',
            'color': 'primary',
            'svg_path': vol_sparkline,
            'link': url_for('admin.history')
        },
        {
            'label': 'Resolved',
            'value': fixed_tickets_count,
            'trend': res_trend,
            'desc': 'Fixed in selected window',
            'color': 'success',
            'svg_path': res_sparkline,
            'link': url_for('admin.history', status='fixed')
        },
        {
            'label': 'Success Rate',
            'value': success_rate,
            'is_percent': True,
            'trend': sr_trend,
            'desc': 'Window resolution efficiency',
            'color': 'info',
            'svg_path': sr_sparkline,
            'link': url_for('admin.history')
        },
        {
            'label': 'Avg. Fix Time',
            'value': avg_res_time,
            'is_hour': True,
            'trend': time_trend,
            'desc': 'Mean TTR for this window',
            'color': 'warning',
            'svg_path': time_sparkline,
            'link': '#trendChartBox'
        }
    ]

    # Current Risks (Always current)
    critical_assets = get_critical_assets(5)

    if request.path.endswith('/api/analytics') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return api_response(success=True, data={'total_tickets': total_tickets,
            'completed_tickets': fixed_tickets_count,
            'open_tickets': total_tickets - fixed_tickets_count,
            'category_data': consolidated_data,
            'avg_resolution_time': avg_res_time,
            'success_rate': success_rate,
            'monthly_trend': trend_data,
            'period': period,
            'advanced_stats': advanced_stats,
            'critical_assets': critical_assets})

    return render_template('admin_analytics.html',
                          total_tickets=total_tickets,
                          fixed_count=fixed_tickets_count,
                          category_data=consolidated_data,
                          avg_res_time=avg_res_time,
                          success_rate=success_rate,
                          monthly_trend=trend_data,
                          period=period,
                          start_date=start_date_str,
                          end_date=end_date_str,
                          advanced_stats=advanced_stats,
                          critical_assets=critical_assets)


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
@handle_api_errors
def edit_user(user_id):
    """Edit user details (AJAX)."""
    target_user = User.query.get_or_404(user_id)
    current_user_id = session.get('user_id')

    if target_user.is_super_admin and current_user_id != target_user.id:
        flash("Unauthorized: Cannot modify Super Admin accounts.", "error")
        abort(403, description="Unauthorized: Cannot modify Super Admin accounts.")

    user = target_user
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    prn = data.get('prn', '').strip()
    
    if not name:
        return api_response(success=False, error="Name cannot be empty.", status=400)
    if not email:
        return api_response(success=False, error="Email cannot be empty.", status=400)
    
    if email != user.email:
        if User.query.filter_by(email=email).first():
            return api_response(success=False, error="Email already registered.", status=400)
            
    user.name = name
    user.email = email
    user.prn = prn
    user.is_admin = data.get('role') == 'admin'
    
    password = data.get('password')
    if password:
        user.set_password(password)
        
    db.session.commit()
    return api_response(success=True, message="User updated successfully")


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
@handle_api_errors
def delete_user(user_id):
    """Delete a user (AJAX)."""
    target_user = User.query.get_or_404(user_id)
    current_user_id = session.get('user_id')

    if target_user.is_super_admin and current_user_id != target_user.id:
        flash("Unauthorized: Cannot modify Super Admin accounts.", "error")
        abort(403, description="Unauthorized: Cannot modify Super Admin accounts.")

    if user_id == current_user_id:
        return api_response(success=False, error="Cannot delete yourself.", status=400)
        
    user = target_user
    db.session.delete(user)
    db.session.commit()
    return api_response(success=True, message="User deleted successfully")


@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@admin_required
@handle_api_errors
def verify_user_manual(user_id):
    """Manually verify a user (AJAX)."""
    target_user = User.query.get_or_404(user_id)
    current_user_id = session.get('user_id')

    if target_user.is_super_admin and current_user_id != target_user.id:
        flash("Unauthorized: Cannot modify Super Admin accounts.", "error")
        abort(403, description="Unauthorized: Cannot modify Super Admin accounts.")

    user = target_user
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    return api_response(success=True, message="User verified successfully")


@admin_bp.route('/tickets/<int:ticket_id>/update-status', methods=['POST'])
@admin_required
@handle_api_errors
def update_ticket_status(ticket_id):
    """Update ticket status (AJAX endpoint)."""
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in Ticket.STATUS_CHOICES:
        return api_response(success=False, error="Invalid status", status=400)
    
    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()
    
    # If marking as fixed or resolved, update asset status and record audit log
    if new_status in [Ticket.STATUS_FIXED, Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED]:
        ticket.fixed_at = datetime.utcnow()
        if not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        if not ticket.verified_by_id and session.get('user_id'):
            ticket.verified_by_id = session['user_id']
        if ticket.asset_id:
            asset = db.session.get(Asset, ticket.asset_id)
            if asset:
                asset.status = Asset.STATUS_WORKING

        supervisor = db.session.get(User, session.get('user_id'))
        supervisor_name = supervisor.name if supervisor else f"Supervisor #{session.get('user_id')}"
        existing_audit = AuditLog.query.filter(
            AuditLog.action == "TICKET_VERIFIED_CLOSED",
            or_(AuditLog.ticket_id == ticket.id, (AuditLog.target_type == 'Ticket') & (AuditLog.target_id == ticket.id))
        ).first()

        if existing_audit:
            existing_audit.user_id = session.get('user_id')
            existing_audit.performed_by_id = session.get('user_id')
            existing_audit.details = f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached."
            existing_audit.timestamp = datetime.utcnow()
            existing_audit.created_at = datetime.utcnow()
        elif ticket.proof_of_completion_url or ticket.proof_image_url:
            audit_entry = AuditLog(
                action="TICKET_VERIFIED_CLOSED",
                details=f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached.",
                user_id=session.get('user_id'),
                target_type="Ticket",
                target_id=ticket.id,
                created_at=datetime.utcnow()
            )
            db.session.add(audit_entry)
    
    db.session.commit()
    
    # Invalidate map cache for affected floor
    if ticket.room_id:
        room = db.session.get(Room, ticket.room_id)
        if room:
            from ...cache import invalidate_floor_cache
            invalidate_floor_cache(room.floor_id)
    
    # Trigger EmailJS notification for ticket update
    send_ticket_email(ticket, action=new_status)
    
    return api_response(
        success=True,
        message=f"Ticket #{ticket.id} marked as {new_status}",
        data={
            'ticket_id': ticket.id,
            'status': ticket.status
        }
    )


@admin_bp.route('/issues/<int:ticket_id>/verify-close', methods=['POST'])
@admin_bp.route('/tickets/<int:ticket_id>/verify-close', methods=['POST'])
@admin_required
@handle_api_errors
def verify_and_close_ticket(ticket_id):
    """
    Supervisor Quality Assurance Verification & Closure Endpoint (Phase 4).
    Enforces Admin authentication and X-Tab-Guard-ID Zero-Trust validation.
    Saves camera/proof image, updates ticket, and commits immutable AuditLog record.
    """
    import os, time, uuid
    from werkzeug.utils import secure_filename

    # Strictly enforce Zero-Trust Tab Guard validation
    client_guard_id = request.headers.get('X-Tab-Guard-ID') or request.form.get('X-Tab-Guard-ID')
    server_guard_id = session.get('tab_guard_id')
    if server_guard_id and client_guard_id != server_guard_id:
        return api_response(success=False, error="Security violation: Zero-Trust Tab Guard mismatch. Please refresh.", status=403)

    ticket = Ticket.query.get_or_404(ticket_id)

    # Validate proof of completion image
    if 'proof_image' not in request.files:
        return api_response(success=False, error="Proof of completion image is required.", status=400)
    file = request.files['proof_image']
    if not file or not file.filename:
        return api_response(success=False, error="A valid proof image file is required.", status=400)
    if not allowed_file(file.filename):
        return api_response(success=False, error="Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.", status=400)

    # Sanitize filename and append unique timestamp/UUID to prevent collisions
    safe_name = secure_filename(file.filename) or 'proof.jpg'
    unique_filename = f"proof_{ticket_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}_{safe_name}"
    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads')), 'proofs')
    os.makedirs(upload_dir, exist_ok=True)
    full_save_path = os.path.join(upload_dir, unique_filename)
    save_webapp_file(file, full_save_path)
    proof_url = f"/static/uploads/proofs/{unique_filename}"

    # Extract supervisor remarks and technician name
    technician_name = (request.form.get('technician_name') or request.form.get('vendor_name') or '').strip() or "On-ground Technician"
    resolution_notes = (request.form.get('resolution_notes') or request.form.get('notes') or '').strip()
    if not resolution_notes:
        return api_response(success=False, error="Supervisor inspection notes are required.", status=400)

    now_utc = datetime.utcnow()
    supervisor_id = session.get('user_id')
    supervisor = db.session.get(User, supervisor_id) if supervisor_id else None
    if not supervisor and session.get('super_admin_email'):
        supervisor = User.query.filter_by(email=session['super_admin_email']).first()
        if supervisor:
            supervisor_id = supervisor.id
    supervisor_name = supervisor.name if supervisor else (session.get('super_admin_email') or f"Supervisor #{supervisor_id}")

    # Atomic ticket update and audit commit
    ticket.status = Ticket.STATUS_RESOLVED
    ticket.assigned_vendor_or_tech_name = technician_name
    ticket.verified_by_id = supervisor_id
    ticket.proof_image_url = proof_url
    ticket.proof_of_completion_url = proof_url
    ticket.completion_photo_filename = unique_filename
    ticket.resolution_notes = resolution_notes
    ticket.resolved_at = now_utc
    ticket.fixed_at = now_utc
    ticket.job_completed_at = now_utc
    ticket.updated_at = now_utc

    if ticket.asset_id:
        asset = db.session.get(Asset, ticket.asset_id)
        if asset:
            asset.status = Asset.STATUS_WORKING

    # Unique Audit Log entry per ticket (maintaining strict 1:1 uniqueness)
    existing_audit = AuditLog.query.filter(
        AuditLog.action == "TICKET_VERIFIED_CLOSED",
        or_(AuditLog.ticket_id == ticket.id, (AuditLog.target_type == 'Ticket') & (AuditLog.target_id == ticket.id))
    ).first()

    if existing_audit:
        existing_audit.user_id = supervisor_id
        existing_audit.performed_by_id = supervisor_id
        existing_audit.details = f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached."
        existing_audit.timestamp = now_utc
        existing_audit.created_at = now_utc
    else:
        audit_entry = AuditLog(
            action="TICKET_VERIFIED_CLOSED",
            details=f"Ticket #{ticket.id} inspected, verified, and closed by Supervisor {supervisor_name} with proof attached.",
            user_id=supervisor_id,
            target_type="Ticket",
            target_id=ticket.id,
            created_at=now_utc
        )
        db.session.add(audit_entry)
    db.session.commit()

    # Invalidate map cache for affected floor
    if ticket.room_id:
        room = db.session.get(Room, ticket.room_id)
        if room:
            from ...cache import invalidate_floor_cache
            invalidate_floor_cache(room.floor_id)

    try:
        send_ticket_email(ticket, action='resolved')
    except Exception:
        pass

    return api_response(
        success=True,
        message=f"Ticket #{ticket.id} verified and committed to audit log.",
        data={
            'ticket_id': ticket.id,
            'status': ticket.status,
            'verified_by': supervisor_name,
            'proof_url': proof_url
        }
    )


@admin_bp.route('/ticket/<int:ticket_id>')
@admin_required
@handle_api_errors
def get_ticket_detail(ticket_id):
    """Get ticket details for modal (AJAX)."""
    ticket = Ticket.query.get_or_404(ticket_id)
    return api_response(success=True, data={'ticket': ticket.to_dict()})


@admin_bp.route('/floor-data/<int:floor_id>')
@admin_required
@handle_api_errors
def get_floor_data(floor_id):
    """Get floor data with room statuses for map (AJAX) - Optimized."""
    from ...cache import cache
    
    cache_key = f'admin_floor_{floor_id}'
    cached = cache.get(cache_key)
    if cached:
        return api_response(success=True, data={**cached})
    
    floor = Floor.query.get_or_404(floor_id)
    
    from sqlalchemy.orm import joinedload
    from ...models import RoomBooking, Timetable, EventBooking
    rooms = Room.query.options(
        joinedload(Room.tickets),
        joinedload(Room.assets),
        joinedload(Room.room_bookings).joinedload(RoomBooking.faculty),
        joinedload(Room.timetables).joinedload(Timetable.faculty),
        joinedload(Room.booked_events).joinedload(EventBooking.faculty)
    ).filter_by(floor_id=floor_id).all()
    
    result = {
        'floor': floor.to_dict(),
        'rooms': [room.to_map_dict() for room in rooms]
    }
    
    cache.set(cache_key, result, timeout=3600)  # 60 minutes
    return api_response(success=True, data={**result})


@admin_bp.route('/api/room-status/<room_number>')
@admin_required
@handle_api_errors
def api_room_status(room_number):
    """Detailed room status for the interactive map (AJAX)."""
    room = Room.query.filter(Room.number.ilike(room_number)).first_or_404()
    
    # Get active ticket (open, assigned, or in-progress)
    active_ticket = Ticket.query.filter(
        Ticket.room_id == room.id,
        Ticket.status.in_([Ticket.STATUS_OPEN, Ticket.STATUS_ASSIGNED, Ticket.STATUS_IN_PROGRESS])
    ).order_by(Ticket.created_at.desc()).first()
    
    return api_response(success=True, data={
        'room': room.to_dict(),
        'active_ticket': active_ticket.to_dict() if active_ticket else None
    })


@admin_bp.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
@admin_required
@handle_api_errors
def delete_ticket(ticket_id):
    """Delete a ticket (AJAX endpoint)."""
    ticket = Ticket.query.get_or_404(ticket_id)
    # Delete associated image if it exists
    if ticket.image_filename:
        import os
        from flask import current_app
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', ticket.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.session.delete(ticket)
    db.session.commit()
    
    return api_response(success=True, message=f"Ticket #{ticket.id} deleted successfully")


@admin_bp.route('/tickets/<int:ticket_id>/rate', methods=['POST'])
@admin_required
@handle_api_errors
def rate_ticket(ticket_id):
    """Rate a professional for a completed job."""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status != Ticket.STATUS_FIXED:
        return api_response(success=False, error="Only fixed tickets can be rated.", status=400)
        
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not rating or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
        return api_response(success=False, error="Rating must be between 1 and 5.", status=400)
        
    ticket.rating = int(rating)
    ticket.rating_comment = comment
    db.session.commit()
    
    return api_response(success=True, message="Rating submitted successfully!")
# ==================== PROFESSIONAL MANAGEMENT ====================

@admin_bp.route('/professionals')
@admin_required
def professionals():
    """Professional Management decommissioned under Supervisor-Verified QA model."""
    flash("Technician account management has been decommissioned under the Supervisor-Verified QA model.", "info")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/professionals/<int:prof_id>/history')
@admin_required
def professional_history(prof_id):
    """View job history for a specific professional."""
    prof = Professional.query.get_or_404(prof_id)
    
    # Get completed jobs
    completed_jobs = Ticket.query.filter_by(
        assigned_professional_id=prof.id,
        status=Ticket.STATUS_FIXED
    ).order_by(Ticket.job_completed_at.desc()).all()
    
    # Get cancelled jobs
    cancelled_jobs = Ticket.query.filter_by(
        cancelled_by_professional_id=prof.id
    ).order_by(Ticket.cancelled_at.desc()).all()
    
    category_names = {
        Professional.CATEGORY_IT: 'IT Technician',
        Professional.CATEGORY_ELECTRICIAN: 'Electrician',
        Professional.CATEGORY_PLUMBER: 'Plumber',
        Professional.CATEGORY_CARPENTER: 'Carpenter'
    }
    
    return render_template('admin/professional_history.html',
                         professional=prof,
                         completed_jobs=completed_jobs,
                         cancelled_jobs=cancelled_jobs,
                         category_name=category_names.get(prof.category, prof.category))


@admin_bp.route('/professionals/add', methods=['GET', 'POST'])
@admin_required
def add_professional():
    """Add a new professional."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        category = request.form.get('category', '').strip()
        password = request.form.get('password', '').strip()
        
        if not all([name, email, category, password]):
            flash('Name, email, category, and password are required.', 'error')
            return render_template('admin/add_professional.html', 
                                 categories=Professional.CATEGORIES,
                                 form_data=request.form)
        
        if category not in Professional.CATEGORIES:
            flash('Invalid category selected.', 'error')
            return render_template('admin/add_professional.html',
                                 categories=Professional.CATEGORIES,
                                 form_data=request.form)
        
        if Professional.query.filter_by(email=email).first():
            flash('A professional with this email already exists.', 'error')
            return render_template('admin/add_professional.html',
                                 categories=Professional.CATEGORIES,
                                 form_data=request.form)
        
        try:
            professional = Professional(
                name=name,
                email=email,
                phone=phone,
                category=category,
                is_active=True
            )
            professional.set_password(password)
            db.session.add(professional)
            db.session.commit()
            
            flash(f'Professional {name} added successfully!', 'success')
            return redirect(url_for('admin.professionals'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding professional: {str(e)}', 'error')
    
    category_names = {
        Professional.CATEGORY_IT: 'IT Technician',
        Professional.CATEGORY_ELECTRICIAN: 'Electrician',
        Professional.CATEGORY_PLUMBER: 'Plumber',
        Professional.CATEGORY_CARPENTER: 'Carpenter'
    }
    
    return render_template('admin/add_professional.html',
                         categories=Professional.CATEGORIES,
                         category_names=category_names)


@admin_bp.route('/professionals/<int:professional_id>/edit', methods=['POST'])
@admin_required
@handle_api_errors
def edit_professional(professional_id):
    """Edit professional details (AJAX)."""
    professional = Professional.query.get_or_404(professional_id)
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    if email != professional.email:
        if Professional.query.filter_by(email=email).first():
            return api_response(success=False, data={'error': "Email already registered."}), 400
    
    professional.name = data.get('name', '').strip()
    professional.email = email
    professional.phone = data.get('phone', '').strip()
    
    new_category = data.get('category')
    if new_category in Professional.CATEGORIES:
        professional.category = new_category
    
    professional.is_active = data.get('is_active', professional.is_active)
    
    password = data.get('password')
    if password:
        professional.set_password(password)
    
    db.session.commit()
    return api_response(success=True, message="Professional updated successfully")


@admin_bp.route('/professionals/<int:professional_id>/delete', methods=['POST'])
@admin_required
@handle_api_errors
def delete_professional(professional_id):
    """Delete a professional (AJAX)."""
    professional = Professional.query.get_or_404(professional_id)
    
    assigned_tickets = Ticket.query.filter_by(
        assigned_professional_id=professional_id
    ).filter(
        Ticket.status.in_([Ticket.STATUS_ASSIGNED, Ticket.STATUS_IN_PROGRESS])
    ).count()
    
    if assigned_tickets > 0:
        return api_response(
            success=False, 
            error=f"Cannot delete professional with {assigned_tickets} active tasks. Reassign tasks first.", 
            status=400
        )
    
    db.session.delete(professional)
    db.session.commit()
    return api_response(success=True, message="Professional deleted successfully")


# ==================== TICKET ASSIGNMENT ====================

@admin_bp.route('/ticket/<int:ticket_id>/assign', methods=['GET', 'POST'])
@admin_required
def assign_ticket(ticket_id):
    """Assign a ticket to a professional."""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if request.method == 'POST':
        professional_id = request.form.get('professional_id', type=int)
        time_limit_hours = request.form.get('time_limit_hours', type=int)
        
        if not professional_id:
            flash('Please select a professional.', 'error')
            return redirect(url_for('admin.assign_ticket', ticket_id=ticket_id))
        
        if not time_limit_hours or time_limit_hours < 1:
            flash('Please enter a valid time limit (minimum 1 hour).', 'error')
            return redirect(url_for('admin.assign_ticket', ticket_id=ticket_id))
        
        professional = db.session.get(Professional, professional_id)
        if not professional or not professional.is_active:
            flash('Selected professional is not available.', 'error')
            return redirect(url_for('admin.assign_ticket', ticket_id=ticket_id))
        
        # Check if professional already has an active task
        active_task = Ticket.query.filter(
            Ticket.assigned_professional_id == professional_id,
            Ticket.status.in_([Ticket.STATUS_ASSIGNED, Ticket.STATUS_IN_PROGRESS])
        ).first()
        
        if active_task:
            flash(f'{professional.name} already has an active task (# {active_task.id}). They must complete it before being assigned a new one.', 'error')
            return redirect(url_for('admin.assign_ticket', ticket_id=ticket_id))
        
        try:
            ticket.assigned_professional_id = professional_id
            ticket.time_limit_hours = time_limit_hours
            ticket.deadline_datetime = datetime.utcnow() + timedelta(hours=time_limit_hours)
            ticket.status = Ticket.STATUS_ASSIGNED
            db.session.commit()
            
            from ...realtime import notify_professional_assigned
            notify_professional_assigned(ticket, professional)
            
            flash(f'Ticket #{ticket_id} assigned to {professional.name}!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning ticket: {str(e)}', 'error')
    
    professionals = Professional.query.filter_by(is_active=True).all()
    
    # Identify professionals with active tasks
    active_statuses = [Ticket.STATUS_ASSIGNED, Ticket.STATUS_IN_PROGRESS]
    busy_professional_ids = {
        t.assigned_professional_id for t in Ticket.query.filter(
            Ticket.status.in_(active_statuses),
            Ticket.assigned_professional_id.isnot(None)
        ).all()
    }
    
    professionals_by_category = {}
    category_names = {
        Professional.CATEGORY_IT: 'IT Technician',
        Professional.CATEGORY_ELECTRICIAN: 'Electrician',
        Professional.CATEGORY_PLUMBER: 'Plumber',
        Professional.CATEGORY_CARPENTER: 'Carpenter'
    }
    
    for prof in professionals:
        cat = prof.category
        if cat not in professionals_by_category:
            professionals_by_category[cat] = {
                'name': category_names.get(cat, cat),
                'professionals': []
            }
        professionals_by_category[cat]['professionals'].append(prof)
    
    suggested_professional_id = None
    best_rating = -1
    target_cat = map_issue_to_category(ticket.issue_type, ticket.description)
    
    matching_profs = [p for p in professionals if p.category == target_cat] if target_cat else professionals
    if not matching_profs: matching_profs = professionals
    
    for p in matching_profs:
        if p.id not in busy_professional_ids and p.overall_rating >= best_rating:
            best_rating = p.overall_rating
            suggested_professional_id = p.id
            
    suggested_professional = db.session.get(Professional, suggested_professional_id) if suggested_professional_id else None
            
    return render_template('admin/assign_ticket.html',
                         ticket=ticket,
                         professionals_by_category=professionals_by_category,
                         category_names=category_names,
                         busy_professional_ids=busy_professional_ids,
                         suggested_professional=suggested_professional)




# ==================== HELP REQUEST MANAGEMENT ====================

@admin_bp.route('/help-requests')
@admin_required
def help_requests():
    """Technician help requests decommissioned under Supervisor-Verified QA model."""
    flash("Technician help requests have been decommissioned under the Supervisor-Verified QA model.", "info")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api/help-request/<int:help_request_id>/respond', methods=['POST'])
@admin_required
@handle_api_errors
def respond_to_help_request(help_request_id):
    """Approve or reject a help request (AJAX)."""
    help_request = HelpRequest.query.get_or_404(help_request_id)
    data = request.get_json()
    
    action = data.get('action')
    helper_professional_id = data.get('helper_professional_id')
    
    if action not in ['approve', 'reject']:
        return api_response(success=False, data={'error': "Invalid action"}), 400
    
    if action == 'approve' and not helper_professional_id:
        return api_response(success=False, data={'error': "Helper professional required for approval"}), 400
    
    admin = db.session.get(User, session['user_id'])
    
    if action == 'approve':
        helper = db.session.get(Professional, helper_professional_id)
        if not helper or not helper.is_active:
            return api_response(success=False, data={'error': "Helper professional not available"}), 400
        
        help_request.status = HelpRequest.STATUS_APPROVED
        help_request.helper_professional_id = helper_professional_id
        help_request.admin_id = admin.id
        help_request.responded_at = datetime.utcnow()
        
        from ...realtime import notify_help_request_approved
        notify_help_request_approved(help_request)
        
    else:
        help_request.status = HelpRequest.STATUS_REJECTED
        help_request.admin_id = admin.id
        help_request.responded_at = datetime.utcnow()
        
        from ...realtime import notify_help_request_rejected
        notify_help_request_rejected(help_request)
    
    db.session.commit()
    return api_response(success=True, message=f"Help request {action}d successfully")


# ==================== ANALYTICS & REPORTS ====================


# Merged analytics into single route /analytics (Line 223)

@admin_bp.route('/reports/export/<string:fmt>')
@admin_required
def export_report(fmt):
    """Export maintenance data as PDF or CSV."""
    import csv
    from flask import make_response
    from io import StringIO
    
    # Fetch filters for report
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = Ticket.query
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Ticket.created_at.between(start_date, end_date))
        except ValueError:
            pass
            
    tickets = query.order_by(Ticket.created_at.desc()).all()
    data = [t.to_dict() for t in tickets]
    if not data:
        flash('No data available for export.', 'info')
        return redirect(url_for('admin.dashboard'))
        
    # Format dates for export
    date_cols = {'created_at', 'updated_at', 'job_started_at', 'job_completed_at', 'fixed_at', 'deadline_datetime'}
    for row in data:
        for col in date_cols:
            val = row.get(col)
            if isinstance(val, datetime):
                row[col] = val.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(val, str) and val:
                try:
                    dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
                    row[col] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass

    if fmt == 'csv':
        output = StringIO()
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=fixlink_report_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    
    elif fmt == 'pdf':
        from fpdf import FPDF
        import os
        from flask import current_app
        
        # Calculate Advanced Analytics for the report
        tech_stats = get_technician_efficiency()
        critical_assets = get_critical_assets(5)
        
        # Global branding colors
        BRAND_BLUE = (11, 77, 140)
        TEXT_DARK = (40, 40, 40)
        TEXT_MUTED = (100, 100, 100)
        SUCCESS_GREEN = (40, 167, 69)
        DANGER_RED = (220, 53, 69)
        
        class PDF(FPDF):
            def header(self):
                # Branding Logo
                logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logo-lm.png')
                if os.path.exists(logo_path):
                    self.image(logo_path, 10, 8, 33)
                
                self.set_font('helvetica', 'B', 15)
                self.set_text_color(*BRAND_BLUE)
                self.cell(80) # Move to the right
                self.cell(110, 10, 'FixLink: Maintenance Performance Report', border=0, align='R')
                self.ln(5)
                self.cell(80)
                self.set_font('helvetica', '', 9)
                self.set_text_color(*TEXT_MUTED)
                self.cell(110, 10, 'MIT-WPU Smart-Room Maintenance Ecosystem', border=0, align='R')
                self.ln(15)
                # Line break
                self.set_draw_color(*BRAND_BLUE)
                self.set_line_width(0.5)
                self.line(10, 32, 200, 32)
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.set_text_color(*TEXT_MUTED)
                self.cell(0, 10, f'MIT-WPU FixLink Confidential | Page {self.page_no()}/{{nb}}', align='C')
                self.cell(0, 10, f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='R')

            def chapter_title(self, label):
                self.set_font('helvetica', 'B', 12)
                self.set_text_color(*BRAND_BLUE)
                self.set_fill_color(240, 245, 255)
                self.cell(0, 10, f'  {label}', ln=True, fill=True)
                self.ln(4)

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- SECTION 1: EXECUTIVE SUMMARY ---
        pdf.chapter_title('Executive Summary')
        
        # KPI Boxes
        total_count = len(data)
        fixed_count = sum(1 for r in data if str(r.get('status', '')).lower() == 'fixed')
        success_rate = round((fixed_count / total_count * 100), 1) if total_count > 0 else 0
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(*TEXT_DARK)
        
        # Stats Row
        col_width = (pdf.w - 20) / 3
        pdf.cell(col_width, 10, 'Total Requests', align='C')
        pdf.cell(col_width, 10, 'Completion Rate', align='C')
        pdf.cell(col_width, 10, 'Critical Assets', align='C')
        pdf.ln(8)
        
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(*BRAND_BLUE)
        pdf.cell(col_width, 10, str(total_count), align='C')
        pdf.cell(col_width, 10, f'{success_rate}%', align='C')
        pdf.cell(col_width, 10, str(len(critical_assets)), align='C')
        pdf.ln(15)
        
        # --- SECTION 2: TECHNICIAN PERFORMANCE ---
        if tech_stats:
            pdf.chapter_title('Technician Efficiency Overview')
            pdf.set_font('helvetica', 'B', 9)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(60, 8, ' Professional Name', border=1, fill=True)
            pdf.cell(40, 8, ' Category', border=1, fill=True)
            pdf.cell(30, 8, ' Closed Jobs', border=1, fill=True, align='C')
            pdf.cell(60, 8, ' Avg. Resolution Time', border=1, fill=True, align='C')
            pdf.ln()
            
            pdf.set_font('helvetica', '', 9)
            pdf.set_text_color(*TEXT_DARK)
            for tech in tech_stats[:5]: # Top 5
                pdf.cell(60, 8, f" {tech['name']}", border=1)
                pdf.cell(40, 8, f" {tech['category'].title()}", border=1)
                pdf.cell(30, 8, str(tech['fixed_count']), border=1, align='C')
                pdf.cell(60, 8, f"{tech['avg_ttr_hours']} hours", border=1, align='C')
                pdf.ln()
            pdf.ln(10)

        # --- SECTION 3: SERVICE CATEGORY DISTRIBUTION ---
        pdf.chapter_title('Service Category Distribution & Visual Analysis')
        category_map = {
            'electrical': 'Electrical & Utilities', 'ac': 'Electrical & Utilities', 
            'lighting': 'Electrical & Utilities', 'light_broken': 'Electrical & Utilities',
            'lift_breakdown': 'Electrical & Utilities', 'lift_not_working': 'Electrical & Utilities',
            'projector': 'IT & AV Systems', 'computer': 'IT & AV Systems',
            'plumbing': 'Plumbing', 'furniture': 'Furniture & Carpentry', 
            'chairs': 'Furniture & Carpentry', 'door_error': 'Furniture & Carpentry',
        }
        
        consolidated_counts = {}
        for row in data:
            group_name = category_map.get(row.get('issue_type'), 'Other')
            consolidated_counts[group_name] = consolidated_counts.get(group_name, 0) + 1
            
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_fill_color(*BRAND_BLUE)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(60, 10, ' Category Group', border=1, fill=True)
        pdf.cell(25, 10, ' Count', border=1, fill=True, align='C')
        pdf.cell(30, 10, ' Distribution', border=1, fill=True, align='C')
        pdf.cell(75, 10, ' Visual Proportion', border=1, fill=True)
        pdf.ln()
        
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(*TEXT_DARK)
        
        sorted_cats = sorted(consolidated_counts.items(), key=lambda x: x[1], reverse=True)
        
        palette = [
            (11, 77, 140),   # #0b4d8c
            (255, 204, 0),   # #ffcc00
            (40, 167, 69),   # #28a745
            (220, 53, 69),   # #dc3545
            (23, 162, 184),  # #17a2b8
            (102, 16, 242),  # #6610f2
            (253, 126, 20)   # #fd7e14
        ]
        
        for idx, (cat, count) in enumerate(sorted_cats):
            pct = (count / total_count * 100) if total_count > 0 else 0
            pdf.cell(60, 8, f" {cat}", border=1)
            pdf.cell(25, 8, str(count), border=1, align='C')
            pdf.cell(30, 8, f"{round(pct, 1)}%", border=1, align='C')
            
            # Draw native vector visual bar cell
            cur_x = pdf.get_x()
            cur_y = pdf.get_y()
            pdf.cell(75, 8, '', border=1)
            
            bar_color = palette[idx % len(palette)]
            pdf.set_fill_color(*bar_color)
            bar_w = max(2, (pct / 100.0) * 70)
            pdf.rect(cur_x + 2.5, cur_y + 2, bar_w, 4, style='F')
            
            pdf.ln()
            
        pdf.ln(10)

        # --- SECTION 4: DETAILED TICKET LOG ---
        pdf.chapter_title('Detailed Maintenance Log')
        
        # Table Header
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_fill_color(*BRAND_BLUE)
        pdf.set_text_color(255, 255, 255)
        
        headers = [('ID', 15), ('Room', 25), ('Status', 30), ('Category', 30), ('Issue Description', 90)]
        for h_text, h_width in headers:
            pdf.cell(h_width, 10, f' {h_text}', border=1, fill=True)
        pdf.ln()
        
        # Table Data
        pdf.set_font('helvetica', '', 8)
        pdf.set_text_color(*TEXT_DARK)
        
        for row in data:
            # Check for page break
            if pdf.get_y() > 260:
                pdf.add_page()
                # Re-add headers on new page
                pdf.set_font('helvetica', 'B', 9)
                pdf.set_fill_color(*BRAND_BLUE)
                pdf.set_text_color(255, 255, 255)
                for h_text, h_width in headers:
                    pdf.cell(h_width, 10, f' {h_text}', border=1, fill=True)
                pdf.ln()
                pdf.set_font('helvetica', '', 8)
                pdf.set_text_color(*TEXT_DARK)

            # Determine status color
            status = str(row.get('status', '')).lower()
            if status == 'fixed':
                pdf.set_text_color(*SUCCESS_GREEN)
            elif status in ['open', 'cancelled']:
                pdf.set_text_color(*DANGER_RED)
            else:
                pdf.set_text_color(*TEXT_DARK)
            
            # Draw row
            h = 8
            pdf.cell(15, h, f" {row.get('id', '')}", border=1)
            pdf.set_text_color(*TEXT_DARK) # Reset color for rest of row
            pdf.cell(25, h, f" {row.get('room_number', 'N/A')}", border=1)
            
            # Status badge (using text color)
            if status == 'fixed': pdf.set_text_color(*SUCCESS_GREEN)
            elif status in ['open', 'cancelled']: pdf.set_text_color(*DANGER_RED)
            pdf.cell(30, h, f" {status.upper()}", border=1)
            pdf.set_text_color(*TEXT_DARK)
            
            pdf.cell(30, h, f" {str(row.get('issue_type', '')).title()}", border=1)
            
            # Issue description (handles long text)
            issue_text = str(row.get('description', row.get('issue_type', '')))
            if len(issue_text) > 55:
                issue_text = issue_text[:52] + "..."
            pdf.cell(90, h, f" {issue_text}", border=1)
            pdf.ln()
            
        # Ensure output is bytes for Flask/Werkzeug response
        pdf_output = pdf.output()
        response = make_response(bytes(pdf_output))
        response.headers["Content-Disposition"] = f"attachment; filename=fixlink_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response

    return redirect(url_for('admin.dashboard'))





# ==================== TIMETABLE IMPORT ====================

@admin_bp.route('/api/timetable/import', methods=['POST'])
@admin_required
@handle_api_errors
def import_timetable():
    """Import timetable from CSV file (Pandas processing)."""
    import pandas as pd
    import io
    import re
    from datetime import datetime, time
    from werkzeug.utils import secure_filename
    from ...models import Room, Timetable

    if 'file' not in request.files:
        return api_response(success=False, error="No file part", status=400)
    
    file = request.files['file']
    if file.filename == '':
        return api_response(success=False, error="No selected file", status=400)
    
    dry_run = request.form.get('dry_run', 'true').lower() == 'true'
    
    try:
        content = file.read().decode('utf-8', errors='replace')
        df = pd.read_csv(io.StringIO(content))
        
        # 1. Normalize headers
        def has_required_cols(columns):
            cols = [str(c).strip().lower() for c in columns]
            has_room = any('room' in c for c in cols)
            has_time = any('time' in c for c in cols)
            return has_room and has_time
            
        if not has_required_cols(df.columns):
            # Try first 3 rows
            for i in range(min(3, len(df))):
                row_vals = df.iloc[i].values
                if has_required_cols(row_vals):
                    df.columns = row_vals
                    df = df.iloc[i+1:].reset_index(drop=True)
                    break
                    
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Find room column
        room_col = next((col for col in df.columns if 'room' in col), None)
        time_col = next((col for col in df.columns if 'time' in col), None)
        
        if not room_col or not time_col:
            return api_response(success=False, error="CSV must contain 'Room No' and 'Time' columns", status=400)
            
        # 2. Forward fill room column (merged cells)
        df[room_col] = df[room_col].ffill()
        
        # 3. Clean and map rooms
        def clean_room(val):
            if pd.isna(val): return None
            match = re.search(r'VY\s*\d+', str(val), re.IGNORECASE)
            return match.group().replace(' ', '').upper() if match else None
            
        df['clean_room'] = df[room_col].apply(clean_room)
        
        # Get all rooms in DB to map string to ID
        rooms = Room.query.all()
        room_map = {r.number.upper(): r.id for r in rooms}
        
        # 4. Clean time column
        def parse_time_range(time_str):
            if pd.isna(time_str): return None, None
            time_str = str(time_str).upper().replace('.', ':').replace(' ', '')
            matches = re.findall(r'(\d{1,2}:\d{2})(AM|PM)?', time_str)
            if len(matches) >= 2:
                try:
                    start_str, start_am_pm = matches[0]
                    end_str, end_am_pm = matches[1]
                    
                    def to_time_obj(t_str, am_pm, is_end=False):
                        h, m = map(int, t_str.split(':'))
                        if h < 12 and (am_pm == 'PM' or (not am_pm and ((h < 8) or is_end))):
                            h += 12
                        elif h == 12 and am_pm == 'AM':
                            h = 0
                        return time(h, m)
                    
                    start_t = to_time_obj(start_str, start_am_pm, False)
                    end_t = to_time_obj(end_str, end_am_pm, True)
                    
                    if end_t <= start_t and end_t.hour < 12:
                        end_t = time(end_t.hour + 12, end_t.minute)
                        
                    return start_t, end_t
                except Exception:
                    return None, None
            return None, None
            
        # 5. Melt the dataframe to extract days
        days = ['mon', 'tue', 'wed', 'thu', 'fri']
        available_days = [day for day in days if day in df.columns]
        day_map = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4}
        
        results = []
        errors = []
        records_to_insert = []
        
        for index, row in df.iterrows():
            room_num = row.get('clean_room')
            if not room_num or room_num not in room_map:
                if room_num:
                    errors.append(f"Row {index+2}: Room '{room_num}' not found in database.")
                continue
                
            room_id = room_map[room_num]
            
            start_t, end_t = parse_time_range(row[time_col])
            if not start_t or not end_t:
                continue
                
            for day_name in available_days:
                cell_val = row.get(day_name)
                if pd.isna(cell_val):
                    continue
                    
                cell_val = str(cell_val).strip()
                if not cell_val:
                    continue
                    
                # Parse Course, Division, Subject
                parts = [p.strip() for p in cell_val.split('\n') if p.strip()]
                if not parts:
                    continue
                    
                course = parts[0]
                division = None
                subject = "Scheduled Class"
                
                div_match = re.search(r'DIV[- ]?([A-Z])', course, re.IGNORECASE)
                if div_match:
                    division = div_match.group(0).upper()
                    
                if len(parts) > 1:
                    subject = parts[1]
                
                tt = Timetable(
                    room_id=room_id,
                    faculty_id=None,
                    day_of_week=day_map[day_name],
                    start_time=start_t,
                    end_time=end_t,
                    subject=subject[:100],
                    course=course[:100],
                    division=division[:50] if division else None
                )
                records_to_insert.append(tt)
                
        summary = {
            'records_parsed': len(records_to_insert),
            'errors': errors[:50],  # Return max 50 errors
            'error_count': len(errors)
        }
        
        if dry_run:
            return api_response(success=True, data=summary)
            
        try:
            db.session.bulk_save_objects(records_to_insert)
            db.session.commit()
            summary['message'] = "Import completed successfully."
            return api_response(success=True, data=summary)
        except Exception as e:
            db.session.rollback()
            return api_response(success=False, error=f"Database error during commit: {str(e)}", status=500)
            
    except Exception as e:
        return api_response(success=False, error=f"Error processing CSV: {str(e)}", status=500)


@admin_bp.route('/api/timetable/delete', methods=['POST'])
@admin_required
@handle_api_errors
def delete_timetable_scoped():
    """
    Deletes timetable entries based on scope:
    - scope='room', room_id=<int>
    - scope='floor', floor_id=<int>
    - scope='building'
    """
    from ...models import Room, Timetable, Floor
    data = request.get_json() or {}
    scope = data.get('scope', '').strip().lower()
    
    if not scope:
        return api_response(success=False, error="Scope parameter ('room', 'floor', or 'building') is required.", status=400)

    if scope == 'room':
        room_id = data.get('room_id')
        if not room_id:
            return api_response(success=False, error="Room ID is required for 'room' scope.", status=400)
        room = db.session.get(Room, room_id)
        if not room:
            return api_response(success=False, error="Room not found.", status=404)
            
        deleted_count = Timetable.query.filter_by(room_id=room_id).delete()
        db.session.commit()
        return api_response(success=True, message=f"Deleted {deleted_count} timetable entries for Room {room.number}.")

    elif scope == 'floor':
        floor_id = data.get('floor_id')
        if not floor_id:
            return api_response(success=False, error="Floor ID is required for 'floor' scope.", status=400)
        floor = db.session.get(Floor, floor_id)
        if not floor:
            return api_response(success=False, error="Floor not found.", status=404)

        room_ids = [r.id for r in Room.query.filter_by(floor_id=floor_id).all()]
        if not room_ids:
            return api_response(success=True, message=f"No rooms found on {floor.name}. 0 records deleted.")

        deleted_count = Timetable.query.filter(Timetable.room_id.in_(room_ids)).delete(synchronize_session=False)
        db.session.commit()
        return api_response(success=True, message=f"Deleted {deleted_count} timetable entries across {floor.name}.")

    elif scope in ['building', 'all', 'whole_building']:
        deleted_count = Timetable.query.delete()
        db.session.commit()
        return api_response(success=True, message=f"Deleted {deleted_count} timetable entries across the entire Vyas building.")

    else:
        return api_response(success=False, error="Invalid scope. Must be 'room', 'floor', or 'building'.", status=400)


@admin_bp.route('/api/assign_faculty/<int:class_id>', methods=['POST'])
@admin_bp.route('/api/assign-faculty/<int:class_id>', methods=['POST'])
@admin_required
@handle_api_errors
def assign_faculty(class_id):
    """
    Assign or update the faculty assigned to a specific Timetable class slot.
    Payload: {"faculty_id": <int or None>}
    """
    from ...models import Timetable, User

    data = request.get_json(silent=True)
    if data is None:
        return api_response(success=False, error="Invalid or missing JSON payload.", status=400)

    if 'faculty_id' not in data:
        return api_response(success=False, error="'faculty_id' is required in JSON payload.", status=400)

    tt = db.session.get(Timetable, class_id)
    if not tt:
        return api_response(success=False, error=f"Class with ID {class_id} not found.", status=404)

    raw_faculty_id = data.get('faculty_id')
    faculty = None
    target_faculty_id = None

    if raw_faculty_id is not None and str(raw_faculty_id).strip() not in ['', '0', 'null', 'None']:
        try:
            target_faculty_id = int(raw_faculty_id)
        except (ValueError, TypeError):
            return api_response(success=False, error="Invalid faculty_id. Must be an integer ID or null.", status=400)

        faculty = db.session.get(User, target_faculty_id)
        if not faculty:
            return api_response(success=False, error=f"Faculty with ID {target_faculty_id} not found.", status=404)

    tt.faculty_id = target_faculty_id

    try:
        db.session.commit()
        faculty_name = faculty.name if faculty else "Unassigned"

        try:
            if tt.room:
                from ...realtime import emit_room_status_change
                emit_room_status_change(tt.room, tt.room.current_occupancy_status)
        except Exception:
            pass

        return api_response(
            success=True,
            message=f"Class '{tt.subject}' successfully assigned to {faculty_name}.",
            data=tt.to_dict()
        )
    except Exception as e:
        db.session.rollback()
        return api_response(
            success=False,
            error=f"Database commit failed: {str(e)}",
            status=500
        )


@admin_bp.route('/api/bulk_assign_faculty', methods=['POST'])
@admin_bp.route('/api/bulk-assign-faculty', methods=['POST'])
@admin_bp.route('/api/timetable/assign-faculty', methods=['POST'])
@admin_required
@handle_api_errors
def bulk_assign_faculty():
    """
    Bulk assign multiple Timetable classes to a single faculty member.
    Payload: {"faculty_id": <int>, "class_ids": [<int>, ...]} or {"faculty_id": <int>, "timetable_ids": [<int>, ...]}
    """
    from ...models import Timetable, User

    data = request.get_json(silent=True)
    if not data:
        return api_response(success=False, error="Invalid or missing JSON payload.", status=400)

    raw_faculty_id = data.get('faculty_id')
    class_ids = data.get('class_ids') or data.get('timetable_ids')

    if not raw_faculty_id:
        return api_response(success=False, error="'faculty_id' is required.", status=400)

    if not class_ids or not isinstance(class_ids, list):
        return api_response(success=False, error="'class_ids' must be a non-empty list of IDs.", status=400)

    try:
        faculty_id = int(raw_faculty_id)
    except (ValueError, TypeError):
        return api_response(success=False, error="Invalid 'faculty_id'. Must be an integer ID.", status=400)

    faculty = db.session.get(User, faculty_id)
    if not faculty:
        return api_response(success=False, error=f"Faculty with ID {faculty_id} not found.", status=404)

    # Sanitize and extract integer class_ids
    valid_class_ids = []
    for cid in class_ids:
        try:
            valid_class_ids.append(int(cid))
        except (ValueError, TypeError):
            continue

    if not valid_class_ids:
        return api_response(success=False, error="No valid class IDs provided in payload.", status=400)

    try:
        # Bulk update setting the faculty_id for all matched records
        updated_count = Timetable.query.filter(Timetable.id.in_(valid_class_ids)).update(
            {Timetable.faculty_id: faculty_id},
            synchronize_session='fetch'
        )

        # Commit the transaction to the database exactly once to ensure optimal performance
        db.session.commit()

        # Emit room status updates if realtime is enabled
        try:
            from ...realtime import emit_room_status_change
            rooms_to_update = db.session.query(Timetable.room_id).filter(Timetable.id.in_(valid_class_ids)).distinct().all()
            for (rid,) in rooms_to_update:
                if rid:
                    from ...models import Room
                    room = db.session.get(Room, rid)
                    if room:
                        emit_room_status_change(room, room.current_occupancy_status)
        except Exception:
            pass

        return api_response(
            success=True,
            message=f"Successfully assigned {updated_count} classes to {faculty.name}.",
            data={
                "faculty_id": faculty_id,
                "faculty_name": faculty.name,
                "updated_count": updated_count
            }
        )
    except Exception as e:
        db.session.rollback()
        return api_response(
            success=False,
            error=f"Database transaction failed during bulk assignment: {str(e)}",
            status=500
        )


# =========================================================================
# PHASE 3: WIDE SUMMARY BULK APPROVAL PIPELINE
# =========================================================================

# =========================================================================
# GHOST PROTOCOL MANAGEMENT CONSOLE
# =========================================================================

@admin_bp.route('/ghost-protocol')
@admin_required
def ghost_protocol():
    """Redirect to unified Faculty Admin Handle Ghost Protocol tab."""
    return redirect(url_for('admin.faculty_admin_handle', tab='ghost'))


@admin_bp.route('/api/ghost-protocol/lift-suspension/<int:faculty_id>', methods=['POST'])
@admin_required
@handle_api_errors
def lift_ghost_suspension(faculty_id):
    """Manually lift a Ghost Protocol ad-hoc suspension for a faculty member."""
    from ...models import NoShowStrike, Notification, SuspensionLog
    user = db.session.get(User, faculty_id)
    if not user:
        return api_response(success=False, error="Faculty not found.", status=404)

    was_suspended = bool(user.adhoc_suspended_until and user.adhoc_suspended_until > datetime.utcnow())
    original_suspended_until = user.adhoc_suspended_until

    data = request.get_json() or {}
    cutoff_30d = datetime.utcnow() - timedelta(days=30)
    strike_count_now = NoShowStrike.query.filter(
        NoShowStrike.faculty_id == faculty_id,
        NoShowStrike.created_at >= cutoff_30d
    ).count()

    # Write permanent audit log BEFORE clearing
    try:
        admin_user_id = session.get('user_id')
        log_entry = SuspensionLog(
            faculty_id=faculty_id,
            event_type=SuspensionLog.EVENT_LIFTED,
            reason=f"Manually lifted by admin (user_id={admin_user_id}). Strikes also {'cleared' if data.get('clear_strikes') else 'retained'}.",
            suspended_until=original_suspended_until,
            strike_count=strike_count_now,
            lifted_by_id=admin_user_id
        )
        db.session.add(log_entry)
    except Exception as le:
        pass  # Non-blocking

    user.adhoc_suspended_until = None
    user.adhoc_suspension_reason = None

    if data.get('clear_strikes'):
        NoShowStrike.query.filter_by(faculty_id=faculty_id).delete()

    try:
        notif = Notification(
            user_id=faculty_id,
            title="Ad-Hoc Booking Privileges Restored",
            message="Your Ad-Hoc room booking suspension has been manually lifted by a Department Administrator. You may now book rooms again.",
            type=Notification.TYPE_SYSTEM,
            link="/faculty/dashboard"
        )
        db.session.add(notif)
    except Exception:
        pass

    db.session.commit()
    return api_response(
        success=True,
        message=f"Suspension for {user.name} has been lifted.",
        data={'faculty_id': faculty_id, 'was_suspended': was_suspended}
    )


@admin_bp.route('/api/ghost-protocol/clear-strikes/<int:faculty_id>', methods=['POST'])
@admin_required
@handle_api_errors
def clear_faculty_strikes(faculty_id):
    """Permanently delete all NoShowStrike records for a faculty member (clean slate)."""
    from ...models import NoShowStrike
    user = db.session.get(User, faculty_id)
    if not user:
        return api_response(success=False, error="Faculty not found.", status=404)

    deleted = NoShowStrike.query.filter_by(faculty_id=faculty_id).delete()
    db.session.commit()
    return api_response(
        success=True,
        message=f"Cleared {deleted} strike record(s) for {user.name}.",
        data={'faculty_id': faculty_id, 'deleted_count': deleted}
    )

@admin_bp.route('/events', methods=['GET'])
@admin_required
def manage_events():
    """Redirect to unified Faculty Admin Handle Event Approvals tab."""
    return redirect(url_for('admin.faculty_admin_handle', tab='events'))

@admin_bp.route('/events/<int:event_id>/approve', methods=['POST'])
@admin_required
@handle_api_errors
def approve_event(event_id):
    from ...models import EventBooking, Timetable, Notification
    from ...realtime import trigger_event
    from datetime import timedelta
    
    event = EventBooking.query.with_for_update().get(event_id)
    if not event:
        return api_response(success=False, error="Event not found.", status=404)
        
    if event.status != 'Pending':
        return api_response(success=False, error=f"Event is already {event.status}.", status=400)
        
    # Overlap check
    overlap_events = EventBooking.query.filter(
        EventBooking.id != event.id,
        EventBooking.status == 'Approved',
        EventBooking.start_date <= event.end_date,
        EventBooking.end_date >= event.start_date,
        EventBooking.start_time < event.end_time,
        EventBooking.end_time > event.start_time
    ).all()
    
    req_room_ids = set(event.get_all_target_room_ids())
    for ev in overlap_events:
        ev_room_ids = set(ev.get_all_target_room_ids())
        if not req_room_ids.isdisjoint(ev_room_ids):
            return api_response(success=False, error=f"Conflict detected with approved event: {ev.title}", status=409)
            
    displaced_faculties = set()
    
    delta = event.end_date - event.start_date
    days_involved = [(event.start_date + timedelta(days=i)).weekday() for i in range(delta.days + 1)]
    
    timetables = Timetable.query.filter(Timetable.room_id.in_(req_room_ids)).all()
    for tt in timetables:
        if tt.day_of_week in days_involved:
            if tt.start_time < event.end_time and tt.end_time > event.start_time:
                if tt.faculty_id:
                    displaced_faculties.add(tt.faculty_id)
                if getattr(tt, 'collaborator_id', None):
                    displaced_faculties.add(tt.collaborator_id)
                
    for fac_id in displaced_faculties:
        if not fac_id or fac_id == event.faculty_id: 
            continue
        notif = Notification(
            user_id=fac_id,
            recipient_role='faculty',
            title="Lecture Displaced by Event",
            message=f"A scheduled lecture has been displaced due to approved event '{event.title}'.",
            type='lecture_displaced'
        )
        db.session.add(notif)
        trigger_event(f'faculty-{fac_id}-alerts', 'notification-received', {'message': notif.message})
        
    event.status = 'Approved'
    
    if event.faculty_id:
        notif = Notification(
            user_id=event.faculty_id,
            recipient_role='faculty',
            title="Event Approved",
            message=f"Your event '{event.title}' has been approved.",
            type='event_approved'
        )
        db.session.add(notif)
        trigger_event(f'faculty-{event.faculty_id}-alerts', 'notification-received', {'message': notif.message})
    
    db.session.commit()
    
    trigger_event('live-map', 'refresh-grid', {})
    
    return api_response(success=True, message="Event approved successfully.")

@admin_bp.route('/events/<int:event_id>/reject', methods=['POST'])
@admin_required
@handle_api_errors
def reject_event(event_id):
    from ...models import EventBooking, Notification
    from ...realtime import trigger_event
    
    data = request.json or {}
    reason = data.get('reason', 'No reason provided.').strip()
    
    event = EventBooking.query.get(event_id)
    if not event:
        return api_response(success=False, error="Event not found.", status=404)
        
    if event.status not in ['Pending', 'Approved']:
        return api_response(success=False, error=f"Event is already {event.status}.", status=400)
        
    was_approved = (event.status == 'Approved')
    event.status = 'Rejected'
    event.rejection_reason = reason
    
    if event.faculty_id:
        title = "Event Revoked / Rejected" if was_approved else "Event Rejected"
        msg = f"Your approved event '{event.title}' was revoked/rejected by administration. Reason: {reason}" if was_approved else f"Your event request '{event.title}' was rejected. Reason: {reason}"
        notif = Notification(
            user_id=event.faculty_id,
            recipient_role='faculty',
            title=title,
            message=msg,
            type='event_rejected'
        )
        db.session.add(notif)
        trigger_event(f'faculty-{event.faculty_id}-alerts', 'notification-received', {'message': notif.message})
    
    db.session.commit()
    
    if was_approved:
        trigger_event('live-map', 'refresh-grid', {})
    
    return api_response(success=True, message="Event rejected successfully." if not was_approved else "Event revoked and rejected successfully.")





