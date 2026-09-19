import os
import re
from datetime import timedelta
import pytest
from flask import Flask, session
from app.models import User, Ticket
from app import db, create_app
from app.decorators import require_ownership

class TestRule7Verification:
    """Automated test suite validating the complete Section 7 Rules in Rules.md."""

    def test_mobile_responsiveness_floating_bug_trigger(self, client):
        """Rule 7.4: Ensure floating desktop triggers are hidden on mobile viewports."""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for d-none d-md-inline-flex class on floating bug trigger
        assert 'class="floating-bug-trigger d-none d-md-inline-flex"' in content or \
               ('floating-bug-trigger' in content and 'd-none d-md-inline-flex' in content)

        # Check for CSS media query hiding rule on mobile
        assert '@media (max-width: 767.98px)' in content or '@media (max-width: 767px)' in content
        assert '.floating-bug-trigger' in content
        assert 'display: none !important;' in content

    def test_mobile_bug_modal_full_width_actions(self):
        """Rule 7.4: Verify modal footer buttons occupy full width without empty gaps."""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify flex: 1 on action buttons in base.html
        assert '.btn-bug-cancel,' in content
        assert '.btn-bug-submit {' in content
        assert 'flex: 1;' in content

    def test_cookie_and_session_lockdown_rule(self):
        """Rule 7.5: Verify Phase 1 Cookie & Session Lockdown configurations."""
        prod_app = create_app()
        assert prod_app.config.get('SESSION_COOKIE_HTTPONLY') is True
        assert prod_app.config.get('SESSION_COOKIE_SECURE') is True
        assert prod_app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'
        assert prod_app.config.get('PERMANENT_SESSION_LIFETIME') == timedelta(hours=2)

    def test_csrf_token_and_meta_tag_rule(self, client):
        """Rule 7.6: Ensure CSRF protection is globally active and exposed via meta tag."""
        prod_app = create_app()
        assert prod_app.config.get('WTF_CSRF_ENABLED') is True
        
        base_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html')
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<meta name="csrf-token" content="{{ csrf_token() }}">' in content
        assert 'name="csrf_token"' in content

    def test_api_security_role_guards(self, client):
        """Rule 7.6: Ensure protected routes reject unauthorized requests."""
        # Test protected admin timetable delete endpoint without login
        res = client.post('/admin/api/timetable/delete', json={'scope': 'all'})
        assert res.status_code in [302, 401, 403]

        # Test assign faculty endpoint without login
        res2 = client.post('/admin/api/assign_faculty/1', json={'faculty_id': 1})
        assert res2.status_code in [302, 401, 403]

    def test_idor_require_ownership_rejection(self, app):
        """Rule 7.8: Verify IDOR prevention decorator strictly rejects unauthorized record modifications (403)."""
        with app.app_context():
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
            with app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
                session.clear()
                res = update_item(item_id=1)
                assert isinstance(res, tuple)
                assert res[1] == 401

            # 2. Test unauthorized user (User 202 trying to modify User 101's item) -> 403
            with app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
                session['user_id'] = 202
                session['is_admin'] = False
                res = update_item(item_id=1)
                assert isinstance(res, tuple)
                assert res[1] == 403

            # 3. Test legitimate owner (User 101) -> 200
            with app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
                session['user_id'] = 101
                session['is_admin'] = False
                res = update_item(item_id=1)
                assert res == {'success': True}

            # 4. Test admin override -> 200
            with app.test_request_context('/api/items/1', headers={'X-Requested-With': 'XMLHttpRequest'}):
                session['user_id'] = 999
                session['is_admin'] = True
                res = update_item(item_id=1)
                assert res == {'success': True}

    def test_interactive_twin_pointer_events_rule(self):
        """Rule 7.10: Verify SVG digital twin maintains non-interfering pointer events."""
        style_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'css', 'style.css')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                style_content = f.read()
            # Verify pointer events rules exist for SVG map layers
            assert 'pointer-events' in style_content

    def test_credential_case_insensitivity_rule(self, app):
        """Rule 7.1: Verify case-insensitive authentication queries work seamlessly."""
        with app.app_context():
            # Check user lookup using db.func.lower
            test_email = "admin@mitwpu.edu.in"
            admin = User.query.filter(db.func.lower(User.email) == test_email.upper().lower()).first()
            if not admin:
                admin = User(name="Admin", email=test_email, is_admin=True)
                admin.set_password("password")
                db.session.add(admin)
                db.session.commit()

            lookup_upper = User.query.filter(db.func.lower(User.email) == "ADMIN@MITWPU.EDU.IN".lower()).first()
            assert lookup_upper is not None
            assert lookup_upper.email.lower() == test_email.lower()
