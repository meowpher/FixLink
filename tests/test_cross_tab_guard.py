import unittest
from app import create_app, db
from app.models import User

class CrossTabGuardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user
        self.user = User(
            name='Test Guard User',
            email='guard.user@mitwpu.edu.in',
            role='student',
            is_verified=True,
            has_accepted_terms=True
        )
        self.user.set_password('Secret123!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_tab_guard_cryptographic_anchor_and_middleware(self):
        # 1. Unauthenticated Phase 3 check
        unauth_status = self.client.get('/api/auth/status')
        self.assertEqual(unauth_status.status_code, 200)
        unauth_json = unauth_status.get_json()
        self.assertFalse(unauth_json['authenticated'])
        self.assertEqual(unauth_json['guard_id'], '')
        self.assertIn('no-store', unauth_status.headers.get('Cache-Control', ''))
        self.assertIn('no-cache', unauth_status.headers.get('Pragma', ''))

        # 2. Login sets tab_guard_id
        res = self.client.post('/login', data={
            'email': 'guard.user@mitwpu.edu.in',
            'password': 'Secret123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.client.session_transaction() as sess:
            tab_guard_id = sess.get('tab_guard_id')
            self.assertIsNotNone(tab_guard_id)
            self.assertEqual(len(tab_guard_id), 32)

        # 3. Authenticated Phase 3 check
        auth_status = self.client.get('/api/auth/status')
        self.assertEqual(auth_status.status_code, 200)
        auth_json = auth_status.get_json()
        self.assertTrue(auth_json['authenticated'])
        self.assertEqual(auth_json['guard_id'], tab_guard_id)
        self.assertIn('no-store', auth_status.headers.get('Cache-Control', ''))
        self.assertIn('no-cache', auth_status.headers.get('Pragma', ''))

        # 4. Response contains X-Tab-Guard-ID header
        home_res = self.client.get('/')
        self.assertIn('X-Tab-Guard-ID', home_res.headers)
        self.assertEqual(home_res.headers['X-Tab-Guard-ID'], tab_guard_id)

        # 5. Phase 2 Middleware Check: POST with wrong / missing X-Tab-Guard-ID is aborted with 403
        conflict_res = self.client.post('/report', data={
            'issue_type': 'electrical',
            'description': 'Test fault'
        })
        self.assertEqual(conflict_res.status_code, 403)
        conflict_json = conflict_res.get_json()
        self.assertEqual(conflict_json.get('error'), 'session_conflict')
        self.assertEqual(conflict_json.get('message'), 'Session corrupted. Please refresh.')

        # 6. Phase 2 Middleware Check: POST with correct X-Tab-Guard-ID header passes middleware
        valid_res = self.client.post('/report', data={
            'issue_type': 'electrical',
            'description': 'Test fault'
        }, headers={'X-Tab-Guard-ID': tab_guard_id})
        self.assertNotEqual(valid_res.status_code, 403)

        # 7. Logout Whitelist Check: /logout passes without needing guard ID and purges session
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('tab_guard_id'))
            self.assertIsNone(sess.get('user_id'))

if __name__ == '__main__':
    unittest.main()
