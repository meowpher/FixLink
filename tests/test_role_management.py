import os
os.environ['TESTING'] = 'True'

import unittest
from datetime import datetime
from app import create_app, db
from app.models import User, Ticket, AuditLog, Building, Floor, Room

class TestRoleManagement(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test_secret_key"
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create Super Admin, Regular Admin, and Faculty users
            self.super_admin = User(
                name="Taha Piplodwala",
                email="taha.piplodwala@mitwpu.edu.in",
                role=User.ROLE_SUPER_ADMIN,
                is_admin=True,
                has_accepted_terms=True
            )
            self.regular_supervisor = User(
                name="Prof. Supervisor",
                email="supervisor@mitwpu.edu.in",
                role=User.ROLE_SUPERVISOR,
                is_admin=True,
                has_accepted_terms=True
            )
            self.faculty = User(
                name="Prof. Faculty Member",
                email="faculty.member@mitwpu.edu.in",
                role=User.ROLE_FACULTY,
                designation="Associate Professor",
                is_admin=False,
                has_accepted_terms=True
            )
            self.faculty2 = User(
                name="Prof. Sharma",
                email="sharma@mitwpu.edu.in",
                role=User.ROLE_FACULTY,
                designation="Assistant Professor",
                is_admin=False,
                has_accepted_terms=True
            )

            db.session.add_all([self.super_admin, self.regular_supervisor, self.faculty, self.faculty2])
            db.session.commit()

            self.super_admin_id = self.super_admin.id
            self.supervisor_id = self.regular_supervisor.id
            self.faculty_id = self.faculty.id
            self.faculty2_id = self.faculty2.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_promote_requires_super_admin(self):
        """Non-superadmin users (regular supervisors or faculty) must receive 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['is_admin'] = True
            sess['is_super_admin'] = False

        res = self.client.post('/admin/users/promote', json={'user_id': self.faculty_id})
        self.assertEqual(res.status_code, 403)

        with self.app.app_context():
            faculty_user = db.session.get(User, self.faculty_id)
            self.assertEqual(faculty_user.role, User.ROLE_FACULTY)

    def test_super_admin_can_promote_faculty_by_id(self):
        """Super Admin can promote a faculty user to SUPERVISOR by user_id."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/promote', json={'user_id': self.faculty_id})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('successfully promoted', data['message'])

        with self.app.app_context():
            promoted_user = db.session.get(User, self.faculty_id)
            self.assertEqual(promoted_user.role, User.ROLE_SUPERVISOR)
            self.assertTrue(promoted_user.is_supervisor)
            self.assertTrue(promoted_user.is_admin)

            # Verify immutable audit log record was committed
            log = AuditLog.query.filter_by(action="USER_PROMOTED_TO_SUPERVISOR", target_id=self.faculty_id).first()
            self.assertIsNotNone(log)
            self.assertIn("promoted to SUPERVISOR", log.details)
            self.assertEqual(log.target_type, "User")

    def test_super_admin_can_promote_faculty_by_email(self):
        """Super Admin can promote a faculty user to SUPERVISOR by email."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/promote', json={'email': 'sharma@mitwpu.edu.in'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        with self.app.app_context():
            promoted_user = db.session.get(User, self.faculty2_id)
            self.assertEqual(promoted_user.role, User.ROLE_SUPERVISOR)
            self.assertTrue(promoted_user.is_supervisor)

    def test_promote_non_existent_user_returns_404(self):
        """Attempting to promote an invalid or non-existent user returns 404."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/promote', json={'user_id': 99999})
        self.assertEqual(res.status_code, 404)

    def test_superadmin_dashboard_renders_role_management_section(self):
        """Super Admin dashboard (/developer) renders Role Management UI with faculty dropdown and supervisors."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True
            sess['super_admin_email'] = 'taha.piplodwala@mitwpu.edu.in'

        res = self.client.get('/developer')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('Role Management: Supervisor Privileges', html)
        self.assertIn('id="promoteNameSearch"', html)
        self.assertIn('id="promoteUserSelect"', html)
        self.assertIn('id="promoteEmailInput"', html)
        self.assertIn('id="supervisorsTable"', html)
        self.assertIn('Prof. Faculty Member', html)
        self.assertIn('Associate Professor', html)
        self.assertIn('Prof. Supervisor', html)
        # Core developer sees Developer Center and developer-only Reported Bugs section
        self.assertIn('Developer Center', html)
        self.assertIn('id="reportedBugsSection"', html)
        self.assertIn('Reported Bugs', html)

        # Non-core admin sees Admin Center and Reported Bugs section is strictly stripped from DOM
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['is_admin'] = True
            sess['is_super_admin'] = True
            sess['super_admin_email'] = 'supervisor@mitwpu.edu.in'

        res_other = self.client.get('/developer')
        self.assertEqual(res_other.status_code, 200)
        html_other = res_other.get_data(as_text=True)
        self.assertIn('Admin Center', html_other)
        self.assertNotIn('Developer Center', html_other)
        self.assertNotIn('id="reportedBugsSection"', html_other)
        self.assertNotIn('Reported Bugs', html_other)
        # Verify standard admin sections remain intact for non-core admin
        self.assertIn('Role Management: Supervisor Privileges', html_other)
        self.assertIn('Quick Access', html_other)


class TestPhase1DatabaseSchemaAndUniversalAccess(unittest.TestCase):
    """Test suite validating Phase 1: Database Schema & Universal Core Access."""

    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test_secret_key"
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # 1. Test User role defaults and allowed values
            self.faculty = User(name="Faculty User", email="faculty@mitwpu.edu.in", prn="FAC1001", has_accepted_terms=True)
            self.supervisor = User(name="Supervisor User", email="supervisor@mitwpu.edu.in", role=User.ROLE_SUPERVISOR, prn="SUP1001", has_accepted_terms=True)
            self.superadmin = User(name="Super Admin User", email="admin@mitwpu.edu.in", role=User.ROLE_SUPER_ADMIN, prn="ADM1001", has_accepted_terms=True)

            db.session.add_all([self.faculty, self.supervisor, self.superadmin])
            db.session.commit()

            self.faculty_id = self.faculty.id
            self.supervisor_id = self.supervisor.id
            self.superadmin_id = self.superadmin.id

            # Vyas building setup for reporting
            bldg = Building(name="Vyas")
            db.session.add(bldg)
            db.session.commit()

            floor = Floor(level=1, name="1st Floor", building_id=bldg.id)
            db.session.add(floor)
            db.session.commit()

            self.room = Room(number="VY101", name="Vyas 101", floor_id=floor.id, room_type="class")
            db.session.add(self.room)
            db.session.commit()
            self.room_id = self.room.id

    def test_user_model_role_definition(self):
        """User model must have role default='FACULTY', designation, and is_active soft delete flag."""
        with self.app.app_context():
            user_default = User(name="Default Role User", email="default@mitwpu.edu.in", designation="Associate Professor")
            db.session.add(user_default)
            db.session.commit()

            self.assertEqual(user_default.role, 'FACULTY')
            self.assertTrue(user_default.is_faculty)
            self.assertFalse(user_default.is_supervisor)
            self.assertFalse(user_default.is_super_admin)
            self.assertEqual(user_default.designation, "Associate Professor")
            self.assertTrue(user_default.is_active)

            # Test soft-delete deprecation
            user_default.is_active = False
            db.session.commit()
            refetched = db.session.get(User, user_default.id)
            self.assertFalse(refetched.is_active)
            self.assertFalse(refetched.to_dict()['is_active'])
            self.assertEqual(refetched.to_dict()['designation'], "Associate Professor")

            # Check supervisor
            sup = db.session.get(User, self.supervisor_id)
            self.assertEqual(sup.role, 'SUPERVISOR')
            self.assertTrue(sup.is_supervisor)

            # Check super admin
            adm = db.session.get(User, self.superadmin_id)
            self.assertEqual(adm.role, 'SUPER_ADMIN')
            self.assertTrue(adm.is_super_admin)

    def test_ticket_model_verification_schema(self):
        """Issue/Ticket model must include verified_by_id, proof_image_url, and resolution_notes."""
        with self.app.app_context():
            ticket = Ticket(
                room_id=self.room_id,
                reporter_id=self.faculty_id,
                reporter_name="Faculty User",
                prn="FAC1001",
                reporter_email="faculty@mitwpu.edu.in",
                issue_type="Electrical",
                description="Power strip sparking",
                status=Ticket.STATUS_OPEN
            )
            db.session.add(ticket)
            db.session.commit()

            # Verify fields exist on model
            self.assertIsNone(ticket.verified_by_id)
            self.assertIsNone(ticket.proof_image_url)
            self.assertIsNone(ticket.resolution_notes)

            # Assign supervisor QA fields
            ticket.verified_by_id = self.supervisor_id
            ticket.proof_image_url = "/static/uploads/proofs/test_proof.jpg"
            ticket.resolution_notes = "Inspected and replaced faulty socket."
            ticket.status = Ticket.STATUS_RESOLVED
            db.session.commit()

            refetched = db.session.get(Ticket, ticket.id)
            self.assertEqual(refetched.verified_by_id, self.supervisor_id)
            self.assertEqual(refetched.verified_by.name, "Supervisor User")
            self.assertEqual(refetched.proof_image_url, "/static/uploads/proofs/test_proof.jpg")
            self.assertEqual(refetched.resolution_notes, "Inspected and replaced faulty socket.")
            self.assertEqual(refetched.status, Ticket.STATUS_RESOLVED)

    def test_audit_log_model_schema_and_immutability(self):
        """AuditLog model must track ID, ticket_id, action, performed_by_id, timestamp, details."""
        with self.app.app_context():
            ticket = Ticket(
                room_id=self.room_id,
                reporter_id=self.faculty_id,
                reporter_name="Faculty User",
                prn="FAC1001",
                reporter_email="faculty@mitwpu.edu.in",
                issue_type="Projector",
                description="HDMI input not working",
                status=Ticket.STATUS_OPEN
            )
            db.session.add(ticket)
            db.session.commit()

            now = datetime.utcnow()
            audit_entry = AuditLog(
                ticket_id=ticket.id,
                action="TICKET_STATUS_CHANGED",
                performed_by_id=self.supervisor_id,
                timestamp=now,
                details=f"Ticket #{ticket.id} status changed from OPEN to RESOLVED by Supervisor User."
            )
            db.session.add(audit_entry)
            db.session.commit()

            self.assertIsNotNone(audit_entry.id)
            self.assertEqual(audit_entry.ticket_id, ticket.id)
            self.assertEqual(audit_entry.action, "TICKET_STATUS_CHANGED")
            self.assertEqual(audit_entry.performed_by_id, self.supervisor_id)
            self.assertEqual(audit_entry.performed_by.name, "Supervisor User")
            self.assertEqual(audit_entry.timestamp, now)
            self.assertIn("OPEN to RESOLVED", audit_entry.details)

            # Test dict serialization
            data = audit_entry.to_dict()
            self.assertEqual(data['ticket_id'], ticket.id)
            self.assertEqual(data['action'], "TICKET_STATUS_CHANGED")
            self.assertEqual(data['performed_by_id'], self.supervisor_id)
            self.assertEqual(data['user_name'], "Supervisor User")
            self.assertIsNotNone(data['timestamp'])

    def test_universal_core_access_report_issue(self):
        """All authenticated ranks (Faculty, Supervisor, Super Admin) must be able to submit tickets via /report."""
        # 1. Faculty report submission
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.faculty_id
            sess['user_role'] = User.ROLE_FACULTY

        res_fac_get = self.client.get('/report')
        self.assertEqual(res_fac_get.status_code, 200)

        res_fac_post = self.client.post('/report', data={
            'room_id': self.room_id,
            'issue_type': 'electrical',
            'description': 'Submitted by Faculty Member'
        }, follow_redirects=True)
        self.assertEqual(res_fac_post.status_code, 200)

        # 2. Supervisor report submission
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR

        res_sup_get = self.client.get('/report')
        self.assertEqual(res_sup_get.status_code, 200)

        res_sup_post = self.client.post('/report', data={
            'room_id': self.room_id,
            'issue_type': 'plumbing',
            'description': 'Submitted by Supervisor User'
        }, follow_redirects=True)
        self.assertEqual(res_sup_post.status_code, 200)

        # 3. Super Admin report submission
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.superadmin_id
            sess['user_role'] = User.ROLE_SUPER_ADMIN
            sess['is_super_admin'] = True

        res_adm_get = self.client.get('/report')
        self.assertEqual(res_adm_get.status_code, 200)

        res_adm_post = self.client.post('/report', data={
            'room_id': self.room_id,
            'issue_type': 'ac',
            'description': 'Submitted by Super Admin User'
        }, follow_redirects=True)
        self.assertEqual(res_adm_post.status_code, 200)

        # Verify all 3 tickets were stored in database
        with self.app.app_context():
            tickets = Ticket.query.filter_by(room_id=self.room_id).all()
            self.assertEqual(len(tickets), 3)
            reporters = [t.reporter_id for t in tickets]
            self.assertIn(self.faculty_id, reporters)
            self.assertIn(self.supervisor_id, reporters)
            self.assertIn(self.superadmin_id, reporters)

    def test_unauthenticated_cannot_access_report_issue(self):
        """Unauthenticated requests must be protected and redirected to login."""
        res_get = self.client.get('/report')
        self.assertIn(res_get.status_code, [302, 401])
        if res_get.status_code == 302:
            self.assertIn('/login', res_get.headers.get('Location', ''))


class TestPhase2RoleManagerAndPaginatedAuditTrail(unittest.TestCase):
    """Test suite validating Phase 2: Super Admin Role Manager (Promote/Demote) & Paginated Audit Trail."""

    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test_secret_key"
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            self.super_admin = User(
                name="Taha Piplodwala",
                email="taha.piplodwala@mitwpu.edu.in",
                role=User.ROLE_SUPER_ADMIN,
                is_admin=True,
                has_accepted_terms=True
            )
            self.supervisor = User(
                name="Prof. Supervisor Deshmukh",
                email="deshmukh@mitwpu.edu.in",
                role=User.ROLE_SUPERVISOR,
                is_admin=True,
                has_accepted_terms=True
            )
            self.faculty = User(
                name="Prof. Kulkarni",
                email="kulkarni@mitwpu.edu.in",
                role=User.ROLE_FACULTY,
                is_admin=False,
                has_accepted_terms=True
            )

            db.session.add_all([self.super_admin, self.supervisor, self.faculty])
            db.session.commit()

            self.super_admin_id = self.super_admin.id
            self.supervisor_id = self.supervisor.id
            self.faculty_id = self.faculty.id

    def test_super_admin_can_demote_supervisor_by_id(self):
        """Super Admin can demote a SUPERVISOR user back to FACULTY by ID."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/demote', json={'user_id': self.supervisor_id})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['role'], 'FACULTY')

        with self.app.app_context():
            demoted_user = db.session.get(User, self.supervisor_id)
            self.assertEqual(demoted_user.role, User.ROLE_FACULTY)
            self.assertFalse(demoted_user.is_admin)

            # Check immutable AuditLog entry
            log = AuditLog.query.filter_by(action="USER_DEMOTED_TO_FACULTY", target_id=self.supervisor_id).first()
            self.assertIsNotNone(log)
            self.assertIn("demoted to FACULTY", log.details)
            self.assertEqual(log.performed_by_id, self.super_admin_id)

    def test_super_admin_can_demote_supervisor_by_email(self):
        """Super Admin can demote a SUPERVISOR user back to FACULTY by email."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/demote', json={'email': 'deshmukh@mitwpu.edu.in'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        with self.app.app_context():
            demoted_user = db.session.get(User, self.supervisor_id)
            self.assertEqual(demoted_user.role, User.ROLE_FACULTY)

    def test_demote_requires_super_admin(self):
        """Regular faculty or unauthenticated users cannot demote supervisors."""
        # Unauthenticated
        res_unauth = self.client.post('/admin/users/demote', json={'user_id': self.supervisor_id})
        self.assertIn(res_unauth.status_code, [302, 403])

        # Faculty session
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.faculty_id
            sess['user_role'] = User.ROLE_FACULTY
            sess['is_super_admin'] = False

        res_fac = self.client.post('/admin/users/demote', json={'user_id': self.supervisor_id})
        self.assertEqual(res_fac.status_code, 403)

    def test_demote_super_admin_is_prevented(self):
        """Safeguard: Demoting a Super Admin account is blocked."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res = self.client.post('/admin/users/demote', json={'user_id': self.super_admin_id})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn("Super Admin accounts cannot be demoted", data['error'])

    def test_audit_trail_view_pagination_strictly_per_page_20(self):
        """Audit trail must paginate using .paginate(page=page, per_page=20) without loading all records."""
        with self.app.app_context():
            # Seed 45 audit log entries
            logs = []
            for i in range(1, 46):
                action = "TICKET_VERIFIED_CLOSED" if i % 2 == 0 else "USER_PROMOTED_TO_SUPERVISOR"
                logs.append(AuditLog(
                    ticket_id=i if i % 2 == 0 else None,
                    action=action,
                    performed_by_id=self.super_admin_id,
                    timestamp=datetime.utcnow(),
                    details=f"Test audit log entry #{i}"
                ))
            db.session.add_all(logs)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_admin'] = True
            sess['is_super_admin'] = True

        # Test Page 1 HTML
        res_p1 = self.client.get('/admin/audit-trail?page=1')
        self.assertEqual(res_p1.status_code, 200)
        html_p1 = res_p1.get_data(as_text=True)
        self.assertIn('Enterprise Audit Trail', html_p1)
        self.assertIn('Paginated (20 records/page)', html_p1)
        self.assertIn('Page 1 of 3', html_p1)

        # Test Page 2 JSON API
        res_p2_json = self.client.get('/admin/audit-trail?page=2&format=json')
        self.assertEqual(res_p2_json.status_code, 200)
        data_p2 = res_p2_json.get_json()
        self.assertTrue(data_p2['success'])
        self.assertEqual(len(data_p2['data']['logs']), 20)
        self.assertEqual(data_p2['data']['pagination']['page'], 2)
        self.assertEqual(data_p2['data']['pagination']['pages'], 3)
        self.assertEqual(data_p2['data']['pagination']['total'], 45)
        self.assertEqual(data_p2['data']['pagination']['per_page'], 20)

        # Test Page 3 JSON API (remaining 5 records)
        res_p3_json = self.client.get('/admin/audit-trail?page=3&format=json')
        self.assertEqual(res_p3_json.status_code, 200)
        data_p3 = res_p3_json.get_json()
        self.assertEqual(len(data_p3['data']['logs']), 5)

        # Test Action Filter
        res_filter = self.client.get('/admin/audit-trail?action=USER_PROMOTED_TO_SUPERVISOR&format=json')
        self.assertEqual(res_filter.status_code, 200)
        data_filter = res_filter.get_json()
        for item in data_filter['data']['logs']:
            self.assertEqual(item['action'], 'USER_PROMOTED_TO_SUPERVISOR')

    def test_audit_trail_requires_admin_access(self):
        """Unauthorized access to /admin/audit-trail is blocked."""
        # Unauthenticated
        res = self.client.get('/admin/audit-trail')
        self.assertIn(res.status_code, [302, 401, 403])

        # Faculty
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.faculty_id
            sess['is_admin'] = False
            sess['user_role'] = User.ROLE_FACULTY

        res_fac = self.client.get('/admin/audit-trail')
        self.assertIn(res_fac.status_code, [302, 403])


if __name__ == '__main__':
    unittest.main()


