from app import db


def test_admin_dashboard_access(client, admin_user, student_user, professional_user):
    """Test that only admins can access the admin dashboard."""
    
    # 1. Unauthenticated request
    response = client.get('/admin/')
    assert response.status_code == 302 # Redirects to login
    
    # 2. Student request
    with client.session_transaction() as sess:
        sess['user_id'] = student_user.id
        sess['is_admin'] = False
    
    response = client.get('/admin/')
    assert response.status_code == 302 # Redirects non-admin to login
    
    # 3. Professional request
    with client.session_transaction() as sess:
        sess.clear()
        sess['professional_id'] = professional_user.id
    
    response = client.get('/admin/')
    assert response.status_code == 302 # Redirects to main login (not recognized as user)
    
    # 4. Admin request
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True
        
    response = client.get('/admin/')
    assert response.status_code == 200 # OK


def test_professional_profile_access(client, professional_user):
    """Test access to the professional profile page and verification of navigation structure."""
    # 1. Unauthenticated request -> redirects to login
    response = client.get('/professional/profile')
    assert response.status_code == 302

    # 2. Professional logged in -> 200 OK
    with client.session_transaction() as sess:
        sess.clear()
        sess['professional_id'] = professional_user.id
        sess['professional_name'] = professional_user.name
        sess['professional_category'] = professional_user.category

    response = client.get('/professional/profile')
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verify Profile content
    assert "My Profile" in html
    assert professional_user.name in html
    assert "Admin Chat Support" in html
    assert "href=\"/professional/profile\"" in html

    # Verify top nav avatar and back button are removed for professionals
    assert "id=\"mobileNavAvatar\"" not in html
    assert "id=\"mobile-topbar-back-btn\"" not in html

    # Verify dashboard renders 200 without the old duplicate card
    dash_response = client.get('/professional/dashboard')
    assert dash_response.status_code == 200
    dash_html = dash_response.get_data(as_text=True)
    # The dashboard now has My Assigned Tasks and Help Requests, but the old sidebar "My Profile" card was removed
    assert "id=\"mobileNavAvatar\"" not in dash_html
    assert "id=\"mobile-topbar-back-btn\"" not in dash_html


def test_bottlesingh_professional_login(client, run_app_context):
    """Test login with Bottle Singh username and fallback password."""
    from app.models import Professional
    with run_app_context:
        prof = Professional.query.filter_by(username='bottlesingh#pro').first()
        if not prof:
            prof = Professional(
                name='Bottle Singh',
                username='bottlesingh#pro',
                email='bottle.singh@fixlink.com',
                phone='2424242424',
                category='it_technician',
                is_active=True
            )
            prof.set_password('2424242424')
            db.session.add(prof)
            db.session.commit()

    # Attempt login via username
    response = client.post('/login', data={
        'email': 'bottlesingh#pro',
        'password': 'anypassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Bottle Singh" in html or "Dashboard" in html or "My Tasks" in html


def test_professional_profile_picture_upload_and_remove(client, professional_user):
    """Test updating and removing professional profile picture via API."""
    with client.session_transaction() as sess:
        sess.clear()
        sess['professional_id'] = professional_user.id
        sess['professional_name'] = professional_user.name
        sess['professional_category'] = professional_user.category

    # 1. Upload valid data URL
    sample_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    res = client.post('/professional/api/profile/picture', json={'avatar': sample_data_url})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['profile_picture'] == sample_data_url

    # 2. View profile page to see image rendered
    page_res = client.get('/professional/profile')
    assert page_res.status_code == 200
    page_html = page_res.get_data(as_text=True)
    assert 'id="profileAvatarImg"' in page_html

    # 3. Remove profile picture
    remove_res = client.post('/professional/api/profile/picture', json={'action': 'remove'})
    assert remove_res.status_code == 200
    remove_data = remove_res.get_json()
    assert remove_data['success'] is True
    assert remove_data['profile_picture'] is None


def test_om_mahadik_credential_guarantee_and_login(client, app):
    """Test that om.mahadik@mitwpu.edu.in can always log in case-insensitively and self-heals."""
    from app import db
    from app.models import User

    # 1. Login with exact email
    res1 = client.post('/login', data={
        'email': 'om.mahadik@mitwpu.edu.in',
        'password': 'omni12345'
    }, follow_redirects=True)
    assert res1.status_code == 200
    html1 = res1.get_data(as_text=True)
    assert "Invalid email or password" not in html1
    with client.session_transaction() as sess:
        assert sess.get('user_email') == 'om.mahadik@mitwpu.edu.in'
        assert sess.get('is_admin') is True
        assert sess.get('is_super_admin') is True

    # 2. Login with uppercase / mixed case email
    with client.session_transaction() as sess:
        sess.clear()
    res2 = client.post('/login', data={
        'email': 'Om.Mahadik@MITWPU.edu.in',
        'password': 'omni12345'
    }, follow_redirects=True)
    assert res2.status_code == 200
    html2 = res2.get_data(as_text=True)
    assert "Invalid email or password" not in html2

    # 3. Even if user was dropped from database, logging in must self-heal and create the account
    with client.session_transaction() as sess:
        sess.clear()
    with app.app_context():
        User.query.filter(db.func.lower(User.email) == 'om.mahadik@mitwpu.edu.in').delete()
        db.session.commit()
        assert User.query.filter(db.func.lower(User.email) == 'om.mahadik@mitwpu.edu.in').first() is None

    res3 = client.post('/login', data={
        'email': 'om.mahadik@mitwpu.edu.in',
        'password': 'omni12345'
    }, follow_redirects=True)
    assert res3.status_code == 200
    html3 = res3.get_data(as_text=True)
    assert "Invalid email or password" not in html3
    with client.session_transaction() as sess:
        assert sess.get('user_email') == 'om.mahadik@mitwpu.edu.in'
        assert sess.get('is_admin') is True


def test_developer_site_no_my_tasks(client, professional_user):
    """Test that 'My Tasks' is strictly absent from the developer site and developer sessions."""
    # 1. Developer session: 'My Tasks' must not appear in Developer Center or any developer view
    with client.session_transaction() as sess:
        sess.clear()
        sess['is_super_admin'] = True
        sess['super_admin_email'] = 'om.mahadik@mitwpu.edu.in'
        sess['user_email'] = 'om.mahadik@mitwpu.edu.in'
        sess['is_admin'] = True

    res = client.get('/developer')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "My Tasks" not in html
    assert "Developer Center" in html

    # 2. Even if professional_id was in session, accessing developer site strips it and excludes 'My Tasks'
    with client.session_transaction() as sess:
        sess['professional_id'] = professional_user.id

    res2 = client.get('/developer')
    assert res2.status_code == 200
    html2 = res2.get_data(as_text=True)
    assert "My Tasks" not in html2

    with client.session_transaction() as sess:
        assert 'professional_id' not in sess


def test_root_redirects_to_login_and_profile_button_present(client, admin_user, professional_user):
    """Test that root URL redirects to /login and profile avatar button is present for all roles."""
    # 1. Root URL redirects to login
    res_root = client.get('/')
    assert res_root.status_code == 302
    assert res_root.headers['Location'].endswith('/login')

    # 2. Unauthenticated protected routes redirect to login
    res_report = client.get('/report')
    assert res_report.status_code == 302
    assert res_report.headers['Location'].endswith('/login')

    # 3. Admin session has profile button and no technician clutter
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True
        sess['user_name'] = admin_user.name
        sess['user_email'] = admin_user.email
        # Simulate stale professional cookie in browser
        sess['professional_id'] = professional_user.id

    res_admin = client.get('/admin/')
    assert res_admin.status_code == 200
    html_admin = res_admin.get_data(as_text=True)

    # Profile button must be present
    assert 'id="navAvatar"' in html_admin
    assert 'id="profileName"' in html_admin
    assert '/logout' in html_admin

    # Technician elements must not be present
    assert 'My Tasks' not in html_admin

    # Residual professional_id was cleaned up by sanitizer hook
    with client.session_transaction() as sess:
        assert 'professional_id' not in sess



