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
            is_verified=True
        )
        self.user.set_password('Secret123!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_tab_guard_cryptographic_anchor_lifecycle(self):
        # 1. Login sets tab_guard_id
        res = self.client.post('/login', data={
            'email': 'guard.user@mitwpu.edu.in',
            'password': 'Secret123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.client.session_transaction() as sess:
            tab_guard_id = sess.get('tab_guard_id')
            self.assertIsNotNone(tab_guard_id)
            self.assertEqual(len(tab_guard_id), 32)  # 16 bytes hex

        # 2. Response contains X-Tab-Guard-ID header
        home_res = self.client.get('/')
        self.assertIn('X-Tab-Guard-ID', home_res.headers)
        self.assertEqual(home_res.headers['X-Tab-Guard-ID'], tab_guard_id)

        # 3. Logout clears session completely
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('tab_guard_id'))
            self.assertIsNone(sess.get('user_id'))

if __name__ == '__main__':
    unittest.main()
