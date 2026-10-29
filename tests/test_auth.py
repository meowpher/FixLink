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


def test_technician_portal_eradication(client, professional_user):
    """Phase 1 Verification: Standalone Technician Portal routes are completely eradicated and logins rejected."""
    # 1. Access to /professional/* returns 404 or redirect to login
    response = client.get('/professional/profile')
    assert response.status_code in [404, 302]

    dash_response = client.get('/professional/dashboard')
    assert dash_response.status_code in [404, 302]

    # 2. On-ground technician credentials cannot log in
    response = client.post('/login', data={
        'email': 'bottlesingh#pro',
        'password': 'anypassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid email or password." in html


def test_om_mahadik_credential_guarantee_and_login(client, app):
    """Test that om.mahadik@mitwpu.edu.in can always log in case-insensitively and self-heals."""
    from app import db
    from app.models import User

    # 1. Login with exact email
    res1 = client.post('/login', data={
        'email': 'om.mahadik@mitwpu.edu.in',
        'password': 'omni12345',
        'accept_terms': '1'
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
        'password': 'omni12345',
        'accept_terms': '1'
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
        'password': 'omni12345',
        'accept_terms': '1'
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


def test_unread_system_notifications(client, admin_user):
    """Test notifications API."""
    # 1. Unauthenticated -> 401
    res = client.get('/api/notifications/recent')
    assert res.status_code == 401

    # 2. Authenticated Admin
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = admin_user.id
        sess['is_admin'] = True

    res = client.get('/api/notifications/recent')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True


def test_terms_compliance_middleware_interceptor(client, app, run_app_context):
    """Verify Phase 1 Middleware Interceptor guards against SSO/API bypass and unconsented access."""
    from app.models import User

    with run_app_context:
        unconsented_user = User(
            name="Unconsented Faculty",
            email="unconsented@mitwpu.edu.in",
            role=User.ROLE_FACULTY,
            is_admin=False,
            has_accepted_terms=False
        )
        unconsented_user.set_password("pass123")
        db.session.add(unconsented_user)
        db.session.commit()
        unconsented_id = unconsented_user.id

    # 1. Web Trap: Authenticated user with has_accepted_terms=False redirected to /onboarding/terms
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = unconsented_id
        sess['user_role'] = User.ROLE_FACULTY

    res_web = client.get('/faculty/dashboard')
    assert res_web.status_code == 302
    assert res_web.headers['Location'].endswith('/onboarding/terms')

    # 2. Whitelist: Accessing /logout, static assets, or onboarding routes is allowed
    res_terms = client.get('/onboarding/terms')
    assert res_terms.status_code == 200

    res_logout = client.get('/logout')
    assert res_logout.status_code == 302
    assert res_logout.headers['Location'].endswith('/login')

    # 3. API Trap: API calls from unconsented users return 403 with {"error": "terms_required", "redirect": "/logout"}
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = unconsented_id
        sess['user_role'] = User.ROLE_FACULTY

    res_api = client.get('/api/notifications/recent')
    assert res_api.status_code == 403
    api_data = res_api.get_json()
    assert api_data['error'] == 'terms_required'
    assert api_data['redirect'] == '/logout'

    # 4. Consented User: Accept terms via /onboarding/accept, then user can freely access protected routes
    res_accept = client.post('/onboarding/accept', data={'accept_terms': '1'})
    assert res_accept.status_code == 302
    assert not res_accept.headers['Location'].endswith('/onboarding/terms')

    # Now accessing web route is allowed without terms redirection
    res_consented_web = client.get('/report')
    assert res_consented_web.status_code == 200


def test_login_scroll_to_accept_ui_structure(client):
    """Phase 2 Test: Verify terms UI components, modal structure, and accessibility."""
    res = client.get('/login')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Verify checkbox and trigger label
    assert 'id="loginTermsCheckbox"' in html
    assert 'data-bs-target="#loginTermsModal"' in html
    assert 'Terms &amp; Conditions' in html or 'Terms & Conditions' in html

    # 2. Verify login submit button exists
    assert 'id="loginSubmitBtn"' in html

    # 3. Verify modal exists with fixed height scrollbody and accept button
    assert 'id="loginTermsModal"' in html
    assert 'id="termsModalScrollBody"' in html
    assert 'terms-modal-body' in html
    assert 'max-height: 60vh' in html
    assert 'id="modalAcceptBtn"' in html

    # 4. Verify Ghost Protocol & DPDP compliance text in modal
    assert 'Ghost Protocol' in html
    assert '15-Minute Grace Period' in html
    assert '30-Day Rolling Window' in html


def test_login_post_requires_accept_terms_and_persists_consent(client, run_app_context):
    """Verify first-time user accepts terms once, and subsequent logins let user in directly."""
    from app.models import User

    with run_app_context:
        test_student = User(
            name="Compliance Student",
            email="compliance.student@mitwpu.edu.in",
            role=User.ROLE_STUDENT,
            is_admin=False,
            is_verified=True,
            has_accepted_terms=False
        )
        test_student.set_password("StudentPass123!")
        db.session.add(test_student)
        db.session.commit()
        stud_id = test_student.id

    # 1. First-time login: Unconsented user is authenticated and routed to /onboarding/terms
    res_first_login = client.post('/login', data={
        'email': 'compliance.student@mitwpu.edu.in',
        'password': 'StudentPass123!'
    }, follow_redirects=False)
    assert res_first_login.status_code == 302
    assert res_first_login.headers['Location'].endswith('/onboarding/terms')

    # Session is established
    with client.session_transaction() as sess:
        assert sess.get('user_id') == stud_id

    # 2. User accepts terms via onboarding endpoint
    res_accept = client.post('/onboarding/accept', data={'accept_terms': '1'}, follow_redirects=False)
    assert res_accept.status_code == 302
    assert not res_accept.headers['Location'].endswith('/onboarding/terms')

    with run_app_context:
        updated_stud = db.session.get(User, stud_id)
        assert updated_stud.has_accepted_terms is True

    # 3. Subsequent login from same email ID: User logs in and goes straight to dashboard without terms prompt
    client.get('/logout')
    res_subsequent_login = client.post('/login', data={
        'email': 'compliance.student@mitwpu.edu.in',
        'password': 'StudentPass123!'
    }, follow_redirects=False)
    assert res_subsequent_login.status_code == 302
    assert not res_subsequent_login.headers['Location'].endswith('/onboarding/terms')
    assert res_subsequent_login.headers['Location'].endswith('/report')


def test_faculty_portal_access_restricted_to_faculty_except_peons(client, app, run_app_context):
    """Verify ONLY non-peon faculty log in to faculty portal, while peons and students log in to /report."""
    from app.models import User

    with run_app_context:
        prof = User(
            name="Prof. Test User",
            email="prof.test@mitwpu.edu.in",
            role=User.ROLE_FACULTY,
            designation="Professor",
            is_active=True,
            is_verified=True,
            has_accepted_terms=True
        )
        prof.set_password("ProfPass123!")

        peon = User(
            name="Peon Test User",
            email="peon.test@mitwpu.edu.in",
            role=User.ROLE_FACULTY,
            designation="Peon",
            is_active=True,
            is_verified=True,
            has_accepted_terms=True
        )
        peon.set_password("PeonPass123!")

        student = User(
            name="Student Test User",
            email="student.test@mitwpu.edu.in",
            role="student",
            prn="1234567890",
            is_active=True,
            is_verified=True,
            has_accepted_terms=True
        )
        student.set_password("StudentPass123!")

        db.session.add_all([prof, peon, student])
        db.session.commit()

    # 1. Faculty (Professor) login -> redirects straight to personal faculty portal (/faculty/dashboard)
    client.get('/logout')
    res_prof_login = client.post('/login', data={
        'email': 'prof.test@mitwpu.edu.in',
        'password': 'ProfPass123!'
    }, follow_redirects=False)
    assert res_prof_login.status_code == 302
    assert res_prof_login.headers['Location'].endswith('/faculty/dashboard')

    # Access faculty dashboard
    res_prof_dash = client.get('/faculty/dashboard')
    assert res_prof_dash.status_code == 200

    # 2. Peon login -> redirects to campus report form (/report), NOT faculty portal
    client.get('/logout')
    res_peon_login = client.post('/login', data={
        'email': 'peon.test@mitwpu.edu.in',
        'password': 'PeonPass123!'
    }, follow_redirects=False)
    assert res_peon_login.status_code == 302
    assert res_peon_login.headers['Location'].endswith('/report')

    # Peon attempts direct access to /faculty/dashboard -> blocked by faculty_login_required
    res_peon_direct = client.get('/faculty/dashboard', follow_redirects=False)
    assert res_peon_direct.status_code == 302
    assert res_peon_direct.headers['Location'].endswith('/report')

    # 3. Student login -> redirects to /report
    client.get('/logout')
    res_student_login = client.post('/login', data={
        'email': 'student.test@mitwpu.edu.in',
        'password': 'StudentPass123!'
    }, follow_redirects=False)
    assert res_student_login.status_code == 302
    assert res_student_login.headers['Location'].endswith('/report')

    # Student attempts direct access to /faculty/dashboard -> blocked
    res_student_direct = client.get('/faculty/dashboard', follow_redirects=False)
    assert res_student_direct.status_code == 302
    assert res_student_direct.headers['Location'].endswith('/report')









