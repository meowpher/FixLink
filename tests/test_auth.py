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
    assert "Open Chat Support" in html
    assert "href=\"/professional/profile\"" in html

    # Verify top nav avatar is removed for professionals
    assert "id=\"mobileNavAvatar\"" not in html

    # Verify dashboard renders 200 without the old duplicate card
    dash_response = client.get('/professional/dashboard')
    assert dash_response.status_code == 200
    dash_html = dash_response.get_data(as_text=True)
    # The dashboard now has My Assigned Tasks and Help Requests, but the old sidebar "My Profile" card was removed
    assert "id=\"mobileNavAvatar\"" not in dash_html
