"""
Main Routes Blueprint - Student Portal and API Endpoints
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash, Response
from werkzeug.utils import secure_filename
from ... import db
from ...models import Building, Floor, Room, Asset, Ticket, User, Notification, Professional
from ...utils import send_ticket_email, ALLOWED_EXTENSIONS, allowed_file, save_webapp_file
from ...decorators import user_login_required, login_required
from ...api_utils import handle_api_errors, api_response

main_bp = Blueprint('main', __name__)

# ALLOWED_EXTENSIONS and allowed_file are defined in file_utils.py (imported above)


@main_bp.route('/google87abaa634db2f80b.html')
def google_verification():
    """Serve Google Search Console HTML verification file."""
    return Response("google-site-verification: google87abaa634db2f80b.html", mimetype="text/html")


@main_bp.route('/robots.txt')
def robots_txt():
    """Serve dynamic, crawl-directive compliant robots.txt."""
    base_url = "https://fixlink26.vercel.app"
    sitemap_url = f"{base_url}/sitemap.xml"
    rendered = render_template('robots.txt', sitemap_url=sitemap_url)
    response = Response(rendered, mimetype='text/plain')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@main_bp.route('/sitemap.xml')
def sitemap_xml():
    """Serve XML sitemap conforming to sitemaps.org schema."""
    base_url = "https://fixlink26.vercel.app"
    today = datetime.utcnow().strftime('%Y-%m-%d')
    pages = [
        {
            "loc": f"{base_url}/",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "1.0"
        },
        {
            "loc": f"{base_url}/login",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9"
        },
        {
            "loc": f"{base_url}/report",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9"
        },
        {
            "loc": f"{base_url}/faculty/dashboard",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.8"
        },
        {
            "loc": f"{base_url}/professional/dashboard",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.8"
        }
    ]
    rendered = render_template('sitemap.xml', pages=pages)
    response = Response(rendered, mimetype='application/xml')
    response.headers['Cache-Control'] = 'public, max-age=43200'
    return response


@main_bp.route('/')
def index():
    """Render home / landing page directly (200 OK) for users and search crawlers."""
    from ..auth.routes import login
    return login()


@main_bp.route('/report', methods=['GET'])
@user_login_required
def report_form():
    """
    Student portal - report room issues with visual map.
    Supports auto-selection via ?room=VY404 query parameter.
    """
    room_param = request.args.get('room', '').strip().upper()
    selected_building = None
    selected_floor = None
    selected_room = None
    
    # Parse room parameter (format: VY### or VY-###)
    if room_param:
        # Remove any hyphen
        room_param = room_param.replace('-', '')
        
        # Look for room number pattern VY###
        if room_param.startswith('VY') and len(room_param) >= 4:
            room_number = room_param
            
            # Find the room
            room = Room.query.filter(Room.number == room_number).first()
            if room:
                selected_room = room.id
                selected_floor = room.floor_id
                selected_building = room.floor.building_id if room.floor else None
    
    # Get Vyas building and floors
    building = Building.query.filter_by(name='Vyas').first()
    floors = []
    rooms_data = []
    if building:
        floors = Floor.query.filter_by(building_id=building.id).order_by(Floor.level).all()
        selected_building = building.id
        
        if selected_floor:
            from ...cache import get_cached_floor_data
            rooms_data = get_cached_floor_data(selected_floor)
    
    issue_types = [
        ('electrical', 'Electrical Issue'),
        ('plumbing', 'Plumbing Issue'),
        ('furniture', 'Furniture/Bench Damage'),
        ('projector', 'Projector/AV Equipment'),
        ('ac', 'Air Conditioning'),
        ('lighting', 'Lighting'),
        ('computer', 'Computer/Lab Equipment'),
        ('cleaning', 'Cleaning Required'),
        ('lift_breakdown', 'Lift Not Working'),
        ('door_error', 'Door Error'),
        ('light_broken', 'Light/Fan Broken'),
        ('other', 'Other')
    ]
    
    user = User.query.get(session['user_id'])
    
    return render_template('report.html',
                         user=user,
                         building=building,
                         floors=floors,
                         issue_types=issue_types,
                         selected_building=selected_building,
                         selected_floor=selected_floor,
                         selected_room=selected_room,
                         room_param=room_param,
                         rooms_data=rooms_data)


@main_bp.route('/report', methods=['POST'])
@user_login_required
def submit_report():
    """
    Submit a new maintenance ticket.
    Handles both AJAX and form submissions.
    """
    user = User.query.get(session['user_id'])
    reporter_name = user.name
    prn = user.prn or 'Admin'
    reporter_email = user.email

    room_id = request.form.get('room_id')
    issue_type = request.form.get('issue_type', '').strip()
    description = request.form.get('description', '').strip()
    
    # Server-side validation
    errors = []
    
    if not room_id:
        errors.append('Room is required')
    
    if not issue_type:
        errors.append('Issue type is required')
    
    if not description:
        errors.append('Description is required')
    
    if errors:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return api_response(success=False, error='; '.join(errors), status=400)
        return render_template('report.html', errors=errors), 400
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            save_webapp_file(file, file_path)
            image_filename = filename
    
    try:
        # Create ticket
        # Ensure IDs are valid integers
        try:
            r_id = int(room_id)
        except (TypeError, ValueError):
            errors.append('Invalid Room ID')
        
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_response(success=False, error='; '.join(errors), status=400)
            user = User.query.get(session['user_id'])
            building = Building.query.filter_by(name='Vyas').first()
            return render_template('report.html', user=user, building=building, errors=errors), 400

        ticket = Ticket(
            room_id=r_id,
            asset_id=None,
            issue_type=issue_type,
            description=description,
            image_filename=image_filename,
            reporter_id=user.id,
            reporter_name=reporter_name,
            prn=prn,
            reporter_email=reporter_email.lower() if reporter_email else 'unknown@mitwpu.edu.in',
            status=Ticket.STATUS_OPEN
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Invalidate map cache for this floor
        room_obj = Room.query.get(r_id)
        if room_obj:
            from app.cache import invalidate_floor_cache
            invalidate_floor_cache(room_obj.floor_id)
        
        # Trigger EmailJS notification for ticket creation
        # (Consider moving this to a background task in production)
        try:
            send_ticket_email(ticket, action='created')
        except Exception as email_err:
            current_app.logger.error(f"Email failed: {str(email_err)}")
        
        # Return JSON for AJAX, redirect for form submission
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return api_response(
                success=True,
                message='Ticket submitted successfully',
                data={'ticket_id': ticket.id},
                ticket_id=ticket.id
            )
        
        return render_template('report.html', 
                             success=True, 
                             ticket_id=ticket.id,
                             user=user,
                             building=Building.query.filter_by(name='Vyas').first())
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        current_app.logger.error(f"Error submitting report: {error_msg}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return api_response(success=False, error=error_msg, status=500)
        user = User.query.get(session['user_id'])
        building = Building.query.filter_by(name='Vyas').first()
        return render_template('report.html', user=user, building=building, errors=[error_msg]), 500


# API Endpoints

@main_bp.route('/api/floors/<int:building_id>', methods=['GET'])
@user_login_required
@handle_api_errors
def get_floors(building_id):
    """Get all floors for a building (JSON)."""
    floors = Floor.query.filter_by(building_id=building_id).order_by(Floor.level).all()
    return api_response(data={'floors': [floor.to_dict() for floor in floors]})


@main_bp.route('/api/rooms/floor/<int:floor_id>', methods=['GET'])
@user_login_required
@handle_api_errors
def get_rooms_by_floor(floor_id):
    """Get all rooms for a floor (JSON) - Optimized with eager loading and caching."""
    from ...cache import get_cached_floor_data
    rooms_data = get_cached_floor_data(floor_id)
    return api_response(data={'rooms': rooms_data})


@main_bp.route('/api/room/<room_number>', methods=['GET'])
@user_login_required
@handle_api_errors
def get_room_by_number(room_number):
    """Get room details by room number (JSON)."""
    room = Room.query.filter_by(number=room_number.upper()).first_or_404()
    return api_response(data={
        'room': {
            **room.to_dict(),
            'status': room.status,
            'has_open_tickets': room.has_open_tickets
        }
    })


@main_bp.route('/api/assets/<int:room_id>', methods=['GET'])
@user_login_required
@handle_api_errors
def get_assets(room_id):
    """Get all assets for a room (JSON)."""
    assets = Asset.query.filter_by(room_id=room_id).all()
    return api_response(data={'assets': [asset.to_dict() for asset in assets]})


@main_bp.route('/api/buildings', methods=['GET'])
@user_login_required
@handle_api_errors
def get_buildings():
    """Get all buildings (JSON)."""
    buildings = Building.query.all()
    return api_response(data={'buildings': [building.to_dict() for building in buildings]})


@main_bp.route('/api/me')
@login_required
@handle_api_errors
def get_me():
    """Return current profile info (user or professional) for the navbar avatar."""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            photo_url = (
                url_for('static', filename=f'uploads/{user.profile_photo}')
                if user.profile_photo else None
            )
            return api_response(data={
                'name': user.name,
                'email': user.email,
                'prn': user.prn or ('Admin' if user.is_admin else ''),
                'photo_url': photo_url,
                'type': 'user'
            })
    
    if 'professional_id' in session:
        professional = Professional.query.get(session['professional_id'])
        if professional:
            photo_url = None
            if hasattr(professional, 'profile_photo') and professional.profile_photo:
                photo_url = url_for('static', filename=f'uploads/{professional.profile_photo}')
            
            return api_response(data={
                'name': professional.name,
                'email': professional.email or '',
                'prn': professional.category.title(), # Use category as ID for professionals
                'photo_url': photo_url,
                'type': 'professional'
            })
            
    return api_response(success=False, error="Not logged in", status=401)


@main_bp.route('/api/notifications', methods=['GET'])
@login_required
@handle_api_errors
def get_notifications():
    """Get notifications for the current user."""
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
    
    return api_response(data={
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': Notification.query.filter_by(user_id=user_id, is_read=False).count()
    })


@main_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
@handle_api_errors
def read_all_notifications():
    """Mark all notifications as read for current user."""
    user_id = session.get('user_id')
    Notification.query.filter_by(user_id=user_id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return api_response(message="All notifications marked as read")


@main_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@handle_api_errors
def read_notification(notification_id):
    """Mark a specific notification as read."""
    user_id = session.get('user_id')
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return api_response(message="Notification marked as read")


@main_bp.route('/api/push/subscribe', methods=['POST'])
@login_required
@handle_api_errors
def push_subscribe():
    """Store Web Push subscription keys."""
    from ...api_utils import validate_json
    data, error = validate_json(['endpoint', 'keys'])
    if error: return error
    
    endpoint = data['endpoint']
    keys = data['keys']
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')
    
    if not endpoint or not p256dh or not auth:
        return api_response(success=False, error="Missing required keys", status=400)
        
    user_id = session.get('user_id')
    prof_id = session.get('professional_id')
    
    from ...models import PushSubscription
    # Update or create
    sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if not sub:
        sub = PushSubscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_id=user_id,
            professional_id=prof_id
        )
        db.session.add(sub)
    else:
        sub.p256dh = p256dh
        sub.auth = auth
        sub.user_id = user_id
        sub.professional_id = prof_id
        
    db.session.commit()
    return api_response(message="Subscription stored successfully")

@main_bp.route('/report-bug', methods=['GET', 'POST'])
def report_bug():
    if request.method == 'POST':
        from ...models import BugReport
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
        
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        file = request.files.get('file')
        origin = request.form.get('origin', '/')
        page_url = request.form.get('page_url', '').strip()
        
        if not title or not description:
            if is_ajax:
                return jsonify({'success': False, 'error': 'Title and description are required.'}), 400
            flash('Title and description are required.', 'error')
            return redirect(url_for('main.report_bug', origin=origin))
            
        if page_url:
            description = f"{description}\n\n[Context URL: {page_url}]"
            
        file_path = None
        file_data_base64 = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"bug_{timestamp}_{filename}"
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
            save_webapp_file(file, full_path)
            file_path = safe_filename
            
            # Read and encode file data as base64 to store in database (works on Vercel)
            try:
                file.seek(0)
                import base64
                file_data_base64 = base64.b64encode(file.read()).decode('utf-8')
            except Exception as e:
                current_app.logger.error(f"Failed to read file for base64 storage: {str(e)}")
            
        # Determine reporter if logged in
        reporter_id = None
        reporter_type = 'guest'
        
        if session.get('user_id'):
            reporter_id = session.get('user_id')
            reporter_type = 'admin' if session.get('is_admin') else 'user'
            if session.get('is_super_admin'):
                reporter_type = 'superadmin'
        elif session.get('professional_id'):
            reporter_id = session.get('professional_id')
            reporter_type = 'professional'
            
        bug = BugReport(
            title=title,
            description=description,
            file_path=file_path,
            file_data=file_data_base64,
            reporter_id=reporter_id,
            reporter_type=reporter_type
        )
        db.session.add(bug)
        db.session.commit()
        
        if is_ajax:
            return jsonify({
                'success': True,
                'message': 'Bug report submitted successfully! Thank you for helping us improve FixLink.'
            })
            
        flash('Bug report submitted successfully! Thank you for your feedback.', 'success')
        # Validate origin to prevent open redirect attacks
        if origin and not origin.startswith('/'):
            origin = url_for('main.index')
        return redirect(origin if origin else url_for('main.index'))
        
    return render_template('report_bug.html')

@main_bp.route('/api/chat/unread_total')
@handle_api_errors
def get_unread_chat_total():
    from ...models import ChatMessage
    
    if not session.get('user_id') and not session.get('professional_id'):
        return api_response(success=True, data={'unread_count': 0})
        
    unread_count = 0
    if session.get('is_admin'):
        # For Admin, get all unread messages sent by professionals to admin
        unread_count = ChatMessage.query.filter_by(
            sender_type=ChatMessage.SENDER_TYPE_PROFESSIONAL,
            receiver_type=ChatMessage.SENDER_TYPE_ADMIN,
            is_read=False
        ).count()
    elif session.get('professional_id'):
        # For Professional, get all unread messages sent by admin to professional
        prof_id = session.get('professional_id')
        unread_count = ChatMessage.query.filter_by(
            sender_type=ChatMessage.SENDER_TYPE_ADMIN,
            receiver_type=ChatMessage.SENDER_TYPE_PROFESSIONAL,
            receiver_id=prof_id,
            is_read=False
        ).count()
        
    return api_response(
        success=True,
        data={'unread_count': unread_count}
    )
