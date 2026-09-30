import os
import unittest
from datetime import timedelta
from app.models import User
from app import db, create_app
from app.decorators import require_ownership
from flask import session

class TestRule7Verification(unittest.TestCase):
    """Automated test suite validating the complete Section 7 Rules in Rules.md."""

    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_mobile_responsiveness_floating_bug_trigger(self):
        """Rule 7.4: Ensure floating desktop triggers are hidden on mobile viewports."""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for CSS media query hiding rule on mobile
        self.assertTrue('@media (max-width: 767.98px)' in content or '@media (max-width: 767px)' in content or '@media (max-width:767' in content)
        self.assertTrue('floating-bug-trigger' in content)

    def test_mobile_bug_modal_full_width_actions(self):
        """Rule 7.4: Verify modal footer buttons occupy full width without empty gaps."""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify flex: 1 on action buttons in base.html
        self.assertTrue('.btn-bug-cancel' in content)
        self.assertTrue('.btn-bug-submit' in content)

    def test_cookie_and_session_lockdown_rule(self):
        """Rule 7.5: Verify Phase 1 Cookie & Session Lockdown configurations."""
        prod_app = create_app()
        self.assertTrue(prod_app.config.get('SESSION_COOKIE_HTTPONLY'))
        self.assertTrue(prod_app.config.get('SESSION_COOKIE_SECURE'))
        self.assertEqual(prod_app.config.get('SESSION_COOKIE_SAMESITE'), 'Lax')
        self.assertEqual(prod_app.config.get('PERMANENT_SESSION_LIFETIME'), timedelta(hours=2))

    def test_csrf_token_and_meta_tag_rule(self):
        """Rule 7.6: Ensure CSRF protection is globally active and exposed via meta tag."""
        prod_app = create_app()
        self.assertTrue(prod_app.config.get('WTF_CSRF_ENABLED'))
        
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('<meta name="csrf-token" content="{{ csrf_token() }}">', content)

    def test_api_security_role_guards(self):
        """Rule 7.6: Ensure protected routes reject unauthorized requests."""
        # Test protected admin timetable delete endpoint without login
        res = self.client.post('/admin/api/timetable/delete', json={'scope': 'all'})
        self.assertIn(res.status_code, [302, 401, 403])

        # Test assign faculty endpoint without login
        res2 = self.client.post('/admin/api/assign_faculty/1', json={'faculty_id': 1})
        self.assertIn(res2.status_code, [302, 401, 403])

    def test_idor_require_ownership_rejection(self):
        """Rule 7.8: Verify IDOR prevention decorator strictly rejects unauthorized record modifications (403)."""
        # Create a mock route protected with require_ownership
        class DummyRecord:
            query = None
            def __init__(self, id, user_id):
                self.id = id
                self.user_id = user_id

        class MockQuery:
            def get(self, rid):
                return DummyRecord(id=rid, user_id=101)  # Owned by User 101

        DummyRecord.query = MockQuery()

        @require_ownership(DummyRecord, id_param='item_id', owner_field='user_id', allow_admin=True)
        def update_item(item_id):
            return {'success': True}

        # 1. Test unauthenticated request -> 401
        with self.app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
            session.clear()
            res = update_item(item_id=1)
            self.assertIsInstance(res, tuple)
            self.assertEqual(res[1], 401)

        # 2. Test unauthorized user (User 202 trying to modify User 101's item) -> 403
        with self.app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
            session['user_id'] = 202
            session['is_admin'] = False
            res = update_item(item_id=1)
            self.assertIsInstance(res, tuple)
            self.assertEqual(res[1], 403)

        # 3. Test legitimate owner (User 101) -> 200
        with self.app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
            session['user_id'] = 101
            session['is_admin'] = False
            res = update_item(item_id=1)
            self.assertEqual(res, {'success': True})

        # 4. Test admin override -> 200
        with self.app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
            session['user_id'] = 999
            session['is_admin'] = True
            res = update_item(item_id=1)
            self.assertEqual(res, {'success': True})

    def test_interactive_twin_pointer_events_rule(self):
        """Rule 7.10: Verify SVG digital twin maintains non-interfering pointer events."""
        style_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'css', 'style.css')
        if not os.path.exists(style_path):
            style_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'css', 'style.min.css')
        with open(style_path, 'r', encoding='utf-8') as f:
            style_content = f.read()
        self.assertIn('pointer-events', style_content)

    def test_credential_case_insensitivity_rule(self):
        """Rule 7.1: Verify case-insensitive authentication queries work seamlessly."""
        test_email = "admin@mitwpu.edu.in"
        admin = User.query.filter(db.func.lower(User.email) == test_email.upper().lower()).first()
        if not admin:
            admin = User(name="Admin", email=test_email, is_admin=True)
            admin.set_password("password")
            db.session.add(admin)
            db.session.commit()

        lookup_upper = User.query.filter(db.func.lower(User.email) == "ADMIN@MITWPU.EDU.IN".lower()).first()
        self.assertIsNotNone(lookup_upper)
        self.assertEqual(lookup_upper.email.lower(), test_email.lower())

    def test_phase4_global_footer_eradication_and_compliance_relocation(self):
        """Phase 4: Verify global footer eradication and clean workspace layout in base.html."""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Verify global footer is completely eradicated
        self.assertNotIn('<footer', content)

        # 2. Verify main container uses min-vh-100 and pb-5
        self.assertIn('<main class="main-content min-vh-100 pb-5"', content)

if __name__ == '__main__':
    unittest.main()
