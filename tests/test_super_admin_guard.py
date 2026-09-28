import os
os.environ['TESTING'] = 'True'

import unittest
from app import create_app, db, SUPER_ADMIN_EMAILS
from app.models import User

class TestSuperAdminGuard(unittest.TestCase):
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
            self.sa_taha = User(name="Taha Piplodwala", email="taha.piplodwala@mitwpu.edu.in", is_admin=True, has_accepted_terms=True)
            self.sa_om = User(name="Om Mahadik", email="om.mahadik@mitwpu.edu.in", is_admin=True, has_accepted_terms=True)
            self.regular_admin = User(name="Regular Admin", email="reg.admin@mitwpu.edu.in", is_admin=True, has_accepted_terms=True)
            self.student = User(name="Normal Student", email="student@mitwpu.edu.in", is_admin=False, has_accepted_terms=True)

            db.session.add_all([self.sa_taha, self.sa_om, self.regular_admin, self.student])
            db.session.commit()

            self.sa_taha_id = self.sa_taha.id
            self.sa_om_id = self.sa_om.id
            self.regular_admin_id = self.regular_admin.id
            self.student_id = self.student.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_is_super_admin_property(self):
        with self.app.app_context():
            taha = db.session.get(User, self.sa_taha_id)
            om = db.session.get(User, self.sa_om_id)
            regular = db.session.get(User, self.regular_admin_id)

            self.assertTrue(taha.is_super_admin)
            self.assertTrue(om.is_super_admin)
            self.assertFalse(regular.is_super_admin)

    def test_regular_admin_cannot_edit_super_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.regular_admin_id
            sess['is_admin'] = True

        res = self.client.post(f'/admin/users/{self.sa_taha_id}/edit', json={
            'name': 'Hacked Name',
            'email': 'taha.piplodwala@mitwpu.edu.in'
        })
        self.assertEqual(res.status_code, 403)

    def test_regular_admin_cannot_delete_super_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.regular_admin_id
            sess['is_admin'] = True

        res = self.client.post(f'/admin/users/{self.sa_taha_id}/delete')
        self.assertEqual(res.status_code, 403)

    def test_super_admin_cannot_edit_another_super_admin(self):
        # Om cannot edit Taha
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.sa_om_id
            sess['is_admin'] = True

        res = self.client.post(f'/admin/users/{self.sa_taha_id}/edit', json={
            'name': 'Tampered Taha',
            'email': 'taha.piplodwala@mitwpu.edu.in'
        })
        self.assertEqual(res.status_code, 403)

    def test_super_admin_can_edit_themselves(self):
        # Taha can edit Taha
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.sa_taha_id
            sess['is_admin'] = True

        res = self.client.post(f'/admin/users/{self.sa_taha_id}/edit', json={
            'name': 'Taha Piplodwala (Updated)',
            'email': 'taha.piplodwala@mitwpu.edu.in'
        })
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            updated = db.session.get(User, self.sa_taha_id)
            self.assertEqual(updated.name, 'Taha Piplodwala (Updated)')

    def test_regular_admin_can_edit_non_super_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.regular_admin_id
            sess['is_admin'] = True

        res = self.client.post(f'/admin/users/{self.student_id}/edit', json={
            'name': 'Updated Student Name',
            'email': 'student@mitwpu.edu.in'
        })
        self.assertEqual(res.status_code, 200)

    def test_admin_users_ui_hides_controls_for_super_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.regular_admin_id
            sess['user_email'] = 'reg.admin@mitwpu.edu.in'
            sess['is_admin'] = True

        res = self.client.get('/admin/users')
        html = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)

        # In admin_users.html, edit button for Taha or Om must NOT be present for regular admin
        self.assertNotIn(f'edit-user-btn" data-id="{self.sa_taha_id}"', html)
        self.assertNotIn(f'edit-user-btn" data-id="{self.sa_om_id}"', html)
        self.assertNotIn(f'deleteUser({self.sa_taha_id}', html)
        self.assertNotIn(f'deleteUser({self.sa_om_id}', html)
        # Static Super Admin badge must be rendered
        self.assertIn('Super Admin', html)
        # Regular admin should have edit button for normal student
        self.assertIn(f'data-id="{self.student_id}"', html)

    def test_superadmin_users_ui_hides_controls_for_all_super_admins(self):
        # Logged in as Om Mahadik
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.sa_om_id
            sess['user_email'] = 'om.mahadik@mitwpu.edu.in'
            sess['is_super_admin'] = True
            sess['is_admin'] = True

        res = self.client.get('/developer/users')
        html = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)

        # Neither Taha nor Om should have edit or delete buttons rendered
        self.assertNotIn(f'btn-edit-user" data-id="{self.sa_taha_id}"', html)
        self.assertNotIn(f'btn-edit-user" \n                                                        data-id="{self.sa_om_id}"', html)
        self.assertNotIn(f'btn-delete-user"\n                                            data-id="{self.sa_om_id}"', html)

        # Both Taha and Om must show static Super Admin badge
        self.assertIn('Super Admin', html)

    def test_bulk_resolve_and_delete_bugs(self):
        from app.models import BugReport
        with self.app.app_context():
            b1 = BugReport(title="Bug 1", description="Desc 1", reporter_type="student", status=BugReport.STATUS_OPEN)
            b2 = BugReport(title="Bug 2", description="Desc 2", reporter_type="faculty", status=BugReport.STATUS_OPEN)
            b3 = BugReport(title="Bug 3", description="Desc 3", reporter_type="guest", status=BugReport.STATUS_OPEN)
            db.session.add_all([b1, b2, b3])
            db.session.commit()
            b1_id, b2_id, b3_id = b1.id, b2.id, b3.id

        # Non super-admin cannot bulk resolve
        res_unauth = self.client.post('/developer/bugs/bulk-resolve', json={'bug_ids': [b1_id, b2_id]})
        self.assertEqual(res_unauth.status_code, 302)  # redirects to login

        # Super admin bulk resolve
        with self.client.session_transaction() as sess:
            sess['is_super_admin'] = True
            sess['super_admin_email'] = 'taha.piplodwala@mitwpu.edu.in'

        res_resolve = self.client.post('/developer/bugs/bulk-resolve', json={'bug_ids': [b1_id, b2_id]}, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res_resolve.status_code, 200)
        self.assertTrue(res_resolve.get_json()['success'])

        with self.app.app_context():
            b1_db = db.session.get(BugReport, b1_id)
            b2_db = db.session.get(BugReport, b2_id)
            b3_db = db.session.get(BugReport, b3_id)
            self.assertEqual(b1_db.status, BugReport.STATUS_RESOLVED)
            self.assertEqual(b2_db.status, BugReport.STATUS_RESOLVED)
            self.assertEqual(b3_db.status, BugReport.STATUS_OPEN)

        # Super admin bulk delete
        res_delete = self.client.post('/developer/bugs/bulk-delete', json={'bug_ids': [b1_id, b3_id]}, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res_delete.status_code, 200)
        self.assertTrue(res_delete.get_json()['success'])

        with self.app.app_context():
            self.assertIsNone(db.session.get(BugReport, b1_id))
            self.assertIsNotNone(db.session.get(BugReport, b2_id))
            self.assertIsNone(db.session.get(BugReport, b3_id))

if __name__ == '__main__':
    unittest.main()
