import pytest
import re
from app import create_app, db
from app.models import User, Ticket
try:
    from scripts.seed_faculties import clean_staff_name, generate_unique_email, extract_staff_data, find_excel_file
except ImportError:
    from seed_faculties import clean_staff_name, generate_unique_email, extract_staff_data, find_excel_file


def test_prefix_stripping():
    assert clean_staff_name("Dr. Anuradha Kanade") == "Anuradha Kanade"
    assert clean_staff_name("Prof. Dr. S.M. Mali") == "S.M. Mali"
    assert clean_staff_name("Mrs. Shruti Godbole") == "Shruti Godbole"
    assert clean_staff_name("Mrs. Shashikala Patil") == "Shashikala Patil"
    assert clean_staff_name("Ms. Aparna Kulkarni") == "Aparna Kulkarni"
    assert clean_staff_name("Mr. Vishal Pawar") == "Vishal Pawar"
    assert clean_staff_name("Dr.Swapna  Saoji") == "Swapna Saoji"
    assert clean_staff_name("Ms.Pooja Unhale ") == "Pooja Unhale"
    assert clean_staff_name("Mr.Apurva Sharma") == "Apurva Sharma"


def test_email_collision_generation():
    existing_emails = {"john.doe@mitwpu.edu.in", "john.doe1@mitwpu.edu.in"}
    loop_emails = set()
    
    # First collision should get counter 2
    email1 = generate_unique_email("John Doe", existing_emails, loop_emails)
    assert email1 == "john.doe2@mitwpu.edu.in"
    assert "john.doe2@mitwpu.edu.in" in loop_emails
    
    # Next call with same name should get counter 3
    email2 = generate_unique_email("John Doe", existing_emails, loop_emails)
    assert email2 == "john.doe3@mitwpu.edu.in"
    
    # Unique name gets clean email
    email3 = generate_unique_email("Jane Smith", existing_emails, loop_emails)
    assert email3 == "jane.smith@mitwpu.edu.in"


def test_extract_staff_data_typo_fix():
    try:
        excel_path = find_excel_file()
    except FileNotFoundError:
        pytest.skip("DoCSA Excel file not present in test environment")
    df = extract_staff_data(excel_path)
    
    assert len(df) == 89
    # Verify typo fixed
    swapna = df[df['name'].str.contains('Swapna', na=False)]
    assert len(swapna) == 1
    assert swapna.iloc[0]['designation'] == "Associate Professor"
    
    # Ensure no 'Asscociate' remains in any row
    assert not df['designation'].str.contains('Asscociate').any()


def test_soft_delete_preserves_fk_integrity(app):
    with app.app_context():
        # Create a faculty user with a ticket
        test_fac = User(
            name="SoftDelete TestFaculty",
            email="softdelete.test@mitwpu.edu.in",
            role='FACULTY',
            is_active=True
        )
        db.session.add(test_fac)
        db.session.flush()
        
        ticket = Ticket(
            room_id=1,
            issue_type="Projector",
            description="Test issue description",
            reporter_id=test_fac.id,
            reporter_name=test_fac.name,
            reporter_email=test_fac.email,
            prn="1049217068",
            status="OPEN"
        )
        db.session.add(ticket)
        db.session.commit()
        
        ticket_id = ticket.id
        fac_id = test_fac.id
        
        # Perform soft delete as done in seed_faculties
        User.query.filter_by(id=fac_id).update({'is_active': False})
        db.session.commit()
        
        # Verify user is inactive
        refreshed_user = User.query.get(fac_id)
        assert refreshed_user.is_active is False
        
        # Verify ticket still exists and FK relationship is intact
        refreshed_ticket = Ticket.query.get(ticket_id)
        assert refreshed_ticket is not None
        assert refreshed_ticket.reporter_id == fac_id
        assert refreshed_ticket.reporter.name == "SoftDelete TestFaculty"


def test_designation_dropdown_ui_and_filtering(client, app):
    """Test Phase 3: Exact-Match UI Dropdown (Bootstrap 5) and designation filtering."""
    with app.app_context():
        # Create an admin user for session login
        admin = User(
            name="Admin Tester",
            email="admin.tester@mitwpu.edu.in",
            role='SUPER_ADMIN',
            is_admin=True,
            is_active=True,
            has_accepted_terms=True
        )
        asst_prof = User(
            name="Test Assistant Prof",
            email="test.asstprof@mitwpu.edu.in",
            role='FACULTY',
            designation="Assistant Professor",
            is_active=True
        )
        full_prof = User(
            name="Test Full Professor",
            email="test.fullprof@mitwpu.edu.in",
            role='FACULTY',
            designation="Professor",
            is_active=True
        )
        assoc_prof = User(
            name="Test Associate Prof",
            email="test.assocprof@mitwpu.edu.in",
            role='FACULTY',
            designation="Associate Professor",
            is_active=True
        )
        dummy_inactive = User(
            name="Test Inactive Dummy",
            email="test.dummy@mitwpu.edu.in",
            role='FACULTY',
            designation="Professor",
            is_active=False
        )
        peon = User(
            name="Test Peon Staff",
            email="test.peon@mitwpu.edu.in",
            role='FACULTY',
            designation="Peon",
            is_active=True
        )
        db.session.add_all([admin, asst_prof, full_prof, assoc_prof, dummy_inactive, peon])
        db.session.commit()
        admin_id = admin.id

    # Log in as admin
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['is_admin'] = True
        sess['is_super_admin'] = True
        sess['user_role'] = 'SUPER_ADMIN'

    # Request the User Management page
    res = client.get('/admin/users')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Verify Bootstrap 5 dropdown button
    assert 'btn-outline-primary' in html
    assert 'Filter by Designation' in html

    # 2. Verify dropdown menu container and Clear Filter
    assert '<ul class="dropdown-menu' in html
    assert '<a class="dropdown-item" href="?">Clear Filter</a>' in html

    # 3. Verify all exact unified requested designations and exact link formatting
    expected_designations = [
        "Professor",
        "Associate Professor",
        "Associate Professor & Program Director",
        "Professor & Program Head",
        "Assistant Professor",
        "PhD Scholar",
        "Lab Assistant",
        "Office Assistant",
        "Executive Officer",
        "Program Office executive",
        "Peon"
    ]

    for desig in expected_designations:
        expected_link = f'<a class="dropdown-item" href="?designation={desig}">{desig}</a>'
        assert expected_link in html, f"Missing expected link: {expected_link}"

    # Verify separate Program Director and standalone Program Head were consolidated
    assert '<a class="dropdown-item" href="?designation=Program Director">' not in html
    assert '<a class="dropdown-item" href="?designation=Program Head">' not in html
    assert '<a class="dropdown-item" href="?designation=Associate Professor & Program Head">' not in html
    assert '<a class="dropdown-item" href="?designation=Assistant Professor & Program Head">' not in html

    # 4. Verify base query excludes soft-deleted dummies
    assert 'Test Inactive Dummy' not in html

    # 5. Test exact-match filtering (NO wildcard overlap between Professor and Assistant/Associate Professor)
    res_prof = client.get('/admin/users?designation=Professor')
    assert res_prof.status_code == 200
    html_prof = res_prof.get_data(as_text=True)
    assert 'Test Full Professor' in html_prof
    assert 'Test Assistant Prof' not in html_prof
    assert 'Test Associate Prof' not in html_prof
    assert 'Test Inactive Dummy' not in html_prof
    assert 'Test Peon Staff' not in html_prof

    # 6. Test Assistant Professor filter
    res_asst = client.get('/admin/users?designation=Assistant Professor')
    assert res_asst.status_code == 200
    html_asst = res_asst.get_data(as_text=True)
    assert 'Test Assistant Prof' in html_asst
    assert 'Test Full Professor' not in html_asst
    assert 'Test Associate Prof' not in html_asst
    assert 'Test Peon Staff' not in html_asst

    # Test Program Director backward compatibility and unified filter
    res_dir = client.get('/admin/users?designation=Associate Professor & Program Director')
    assert res_dir.status_code == 200

    res_dir_legacy = client.get('/admin/users?designation=Program Director')
    assert res_dir_legacy.status_code == 200

    # Test Program Head unified filter
    res_head = client.get('/admin/users?designation=Professor & Program Head')
    assert res_head.status_code == 200

    res_head_legacy = client.get('/admin/users?designation=Program Head')
    assert res_head_legacy.status_code == 200

    # 7. Test clear filter
    res_cleared = client.get('/admin/users?')
    assert res_cleared.status_code == 200
    html_cleared = res_cleared.get_data(as_text=True)
    assert 'Test Full Professor' in html_cleared
    assert 'Test Assistant Prof' in html_cleared
    assert 'Test Associate Prof' in html_cleared
    assert 'Test Peon Staff' in html_cleared
    assert 'Test Inactive Dummy' not in html_cleared

    # 8. Test Superadmin developer users view (/developer/users)
    res_dev = client.get('/developer/users')
    assert res_dev.status_code == 200
    html_dev = res_dev.get_data(as_text=True)
    assert 'Filter by Designation' in html_dev
    assert '<a class="dropdown-item" href="?">Clear Filter</a>' in html_dev
    assert 'Test Inactive Dummy' not in html_dev
    for desig in expected_designations:
        expected_link = f'<a class="dropdown-item" href="?designation={desig}">{desig}</a>'
        assert expected_link in html_dev, f"Missing expected link in developer view: {expected_link}"

    # Exact match filter in developer users
    res_dev_prof = client.get('/developer/users?designation=Professor')
    assert res_dev_prof.status_code == 200
    html_dev_prof = res_dev_prof.get_data(as_text=True)
    assert 'Test Full Professor' in html_dev_prof
    assert 'Test Assistant Prof' not in html_dev_prof
    assert 'Test Associate Prof' not in html_dev_prof
    assert 'Test Inactive Dummy' not in html_dev_prof


def test_superadmin_developer_role_filtering(client, app):
    """Test sidebar role filtering for Students, Faculty, and Admins in /developer/users."""
    with app.app_context():
        # Clean existing test users if any, or create specific set
        admin_user = User(
            name="Role Test Super Admin",
            email="role.superadmin@mitwpu.edu.in",
            role='SUPER_ADMIN',
            is_admin=True,
            is_active=True,
            has_accepted_terms=True
        )
        student_user = User(
            name="Role Test Student",
            email="role.student@mitwpu.edu.in",
            role='student',
            prn="1032239999",
            is_active=True
        )
        faculty_user = User(
            name="Role Test Faculty",
            email="role.faculty@mitwpu.edu.in",
            role='FACULTY',
            designation="Professor",
            is_active=True
        )
        db.session.add_all([admin_user, student_user, faculty_user])
        db.session.commit()
        admin_id = admin_user.id

    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['is_admin'] = True
        sess['is_super_admin'] = True
        sess['user_role'] = 'SUPER_ADMIN'

    # 1. All Users
    res_all = client.get('/developer/users')
    assert res_all.status_code == 200
    html_all = res_all.get_data(as_text=True)
    assert 'All Users' in html_all
    assert 'Role Test Student' in html_all
    assert 'Role Test Faculty' in html_all
    assert 'Role Test Super Admin' in html_all

    # 2. Filter by Students
    res_student = client.get('/developer/users?role=student')
    assert res_student.status_code == 200
    html_student = res_student.get_data(as_text=True)
    assert 'Students Directory' in html_student
    assert 'Role Test Student' in html_student
    assert 'Role Test Faculty' not in html_student
    assert 'Role Test Super Admin' not in html_student

    # 3. Filter by Faculty
    res_faculty = client.get('/developer/users?role=faculty')
    assert res_faculty.status_code == 200
    html_faculty = res_faculty.get_data(as_text=True)
    assert 'Faculty Members' in html_faculty
    assert 'Role Test Faculty' in html_faculty
    assert 'Role Test Student' not in html_faculty
    assert 'Role Test Super Admin' not in html_faculty

    # 4. Filter by Admins
    res_admin = client.get('/developer/users?role=admin')
    assert res_admin.status_code == 200
    html_admin = res_admin.get_data(as_text=True)
    assert 'Administrators' in html_admin
    assert 'Role Test Super Admin' in html_admin
    assert 'Role Test Student' not in html_admin
    assert 'Role Test Faculty' not in html_admin


