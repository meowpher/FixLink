import os
os.environ['TESTING'] = 'True'

import unittest
import io
from datetime import datetime
from PIL import Image
from app import create_app, db
from app.models import User, Ticket, Room, Floor, Building, AuditLog

class TestSupervisorWorkspace(unittest.TestCase):
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

            # Create Super Admin, Supervisor, and Faculty
            self.super_admin = User(
                name="Taha Piplodwala",
                email="taha.piplodwala@mitwpu.edu.in",
                role=User.ROLE_SUPER_ADMIN,
                is_admin=True,
                has_accepted_terms=True
            )
            self.supervisor = User(
                name="Prof. Sharma (Supervisor)",
                email="sharma@mitwpu.edu.in",
                role=User.ROLE_SUPERVISOR,
                is_admin=True,
                has_accepted_terms=True
            )
            self.faculty = User(
                name="Prof. Verma (Faculty)",
                email="verma@mitwpu.edu.in",
                role=User.ROLE_FACULTY,
                is_admin=False,
                has_accepted_terms=True
            )

            db.session.add_all([self.super_admin, self.supervisor, self.faculty])
            db.session.commit()

            # Create building, floor, and room
            bldg = Building(name="Saraswati Bhavan")
            db.session.add(bldg)
            db.session.commit()

            floor = Floor(level=3, name="3rd Floor", building_id=bldg.id)
            db.session.add(floor)
            db.session.commit()

            self.room = Room(number="304", name="Classroom 304", floor_id=floor.id, room_type="class")
            db.session.add(self.room)
            db.session.commit()

            # Create tickets: 1 OPEN, 1 IN_PROGRESS, 1 RESOLVED, 1 CLOSED
            self.ticket_open = Ticket(
                room_id=self.room.id,
                reporter_id=self.faculty.id,
                reporter_name=self.faculty.name,
                prn="1032200001",
                reporter_email=self.faculty.email,
                issue_type="Electrical",
                description="Projector power socket flickering in room 304",
                status=Ticket.STATUS_OPEN,
                complexity=Ticket.COMPLEXITY_HIGH
            )
            self.ticket_in_progress = Ticket(
                room_id=self.room.id,
                reporter_id=self.faculty.id,
                reporter_name=self.faculty.name,
                prn="1032200001",
                reporter_email=self.faculty.email,
                issue_type="Plumbing",
                description="Water cooler tap dripping",
                status=Ticket.STATUS_IN_PROGRESS,
                complexity=Ticket.COMPLEXITY_MEDIUM
            )
            self.ticket_resolved = Ticket(
                room_id=self.room.id,
                reporter_id=self.faculty.id,
                reporter_name=self.faculty.name,
                prn="1032200001",
                reporter_email=self.faculty.email,
                issue_type="IT",
                description="Old resolved issue with Wi-Fi router",
                status=Ticket.STATUS_RESOLVED,
                complexity=Ticket.COMPLEXITY_LOW
            )

            db.session.add_all([self.ticket_open, self.ticket_in_progress, self.ticket_resolved])
            db.session.commit()

            self.super_admin_id = self.super_admin.id
            self.supervisor_id = self.supervisor.id
            self.faculty_id = self.faculty.id
            self.ticket_open_id = self.ticket_open.id
            self.ticket_prog_id = self.ticket_in_progress.id
            self.ticket_res_id = self.ticket_resolved.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_unauthenticated_cannot_access_supervisor_dashboard(self):
        """Unauthenticated requests must be redirected to login (or 401 for ajax)."""
        res = self.client.get('/supervisor/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_faculty_cannot_access_supervisor_dashboard(self):
        """Standard faculty without supervisor privilege receive 403 or redirect to report form."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.faculty_id
            sess['user_role'] = User.ROLE_FACULTY
            sess['is_admin'] = False

        res = self.client.get('/supervisor/dashboard')
        # Standard request redirects to report_form with flash message
        self.assertEqual(res.status_code, 302)
        self.assertIn('/report', res.headers['Location'])

        # AJAX request receives 403
        res_ajax = self.client.get('/supervisor/dashboard', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res_ajax.status_code, 403)

    def test_supervisor_and_superadmin_can_access_dashboard(self):
        """Supervisors and Super Admins can access /supervisor/dashboard."""
        # Supervisor
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True

        res = self.client.get('/supervisor/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Verification Console", html)
        self.assertIn("Verify &amp; Log Completion", html)

        # Super Admin
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.super_admin_id
            sess['is_super_admin'] = True

        res_sa = self.client.get('/supervisor/dashboard')
        self.assertEqual(res_sa.status_code, 200)

    def test_dashboard_displays_only_active_tickets_and_excludes_resolved(self):
        """Only OPEN and IN_PROGRESS tickets appear. RESOLVED tickets must be excluded."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True

        res = self.client.get('/supervisor/dashboard')
        html = res.get_data(as_text=True)

        # Active tickets must be present
        self.assertIn("Projector power socket flickering in room 304", html)
        self.assertIn("Water cooler tap dripping", html)
        # Resolved ticket must NOT be present
        self.assertNotIn("Old resolved issue with Wi-Fi router", html)
        # Global system analytics charts must be excluded
        self.assertNotIn("id=\"trendChart\"", html)
        self.assertNotIn("id=\"statusDistributionChart\"", html)

    def test_verify_and_close_ticket_endpoint(self):
        """POST /supervisor/issues/<id>/verify-close updates ticket, uses UUID prefix, and writes AuditLog."""
        import re
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True
            sess['tab_guard_id'] = 'test_zero_trust_guard_xyz'

        test_img = (io.BytesIO(b"fake_image_bytes"), "completion_proof.jpg")

        res = self.client.post(
            f'/supervisor/issues/{self.ticket_open_id}/verify-close',
            data={
                'technician_name': 'Ramesh Electricals',
                'proof_image': test_img,
                'resolution_notes': 'Inspected room 304. New switchboard socket installed and load tested.'
            },
            content_type='multipart/form-data',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'X-Tab-Guard-ID': 'test_zero_trust_guard_xyz'
            }
        )

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        with self.app.app_context():
            updated_ticket = db.session.get(Ticket, self.ticket_open_id)
            self.assertEqual(updated_ticket.status, Ticket.STATUS_RESOLVED)
            self.assertEqual(updated_ticket.verified_by_id, self.supervisor_id)
            self.assertEqual(updated_ticket.resolution_notes, 'Inspected room 304. New switchboard socket installed and load tested.')
            self.assertEqual(updated_ticket.assigned_vendor_or_tech_name, 'Ramesh Electricals')
            self.assertIsNotNone(updated_ticket.resolved_at)

            # Verify UUID prefix format: <uuid>_<safe_filename>
            self.assertIsNotNone(updated_ticket.completion_photo_filename)
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_completion_proof\.jpg$'
            self.assertTrue(re.match(uuid_pattern, updated_ticket.completion_photo_filename))

            # Check immutable AuditLog entry
            log = AuditLog.query.filter_by(action="TICKET_VERIFIED_CLOSED", target_id=self.ticket_open_id).first()
            self.assertIsNotNone(log)
            self.assertIn("inspected, verified, and closed by Supervisor", log.details)
            self.assertIn("with proof attached", log.details)

    def test_verify_and_close_enforces_zero_trust_tab_guard(self):
        """Mismatched or missing X-Tab-Guard-ID header must return 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True
            sess['tab_guard_id'] = 'strict_server_guard_id_123'

        test_img = (io.BytesIO(b"fake_image_bytes"), "proof.jpg")

        # 1. Missing header / wrong header
        res_mismatch = self.client.post(
            f'/supervisor/issues/{self.ticket_prog_id}/verify-close',
            data={
                'technician_name': 'Vendor',
                'proof_image': test_img,
                'resolution_notes': 'Inspected.'
            },
            content_type='multipart/form-data',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'X-Tab-Guard-ID': 'wrong_client_guard_id'
            }
        )
        self.assertEqual(res_mismatch.status_code, 403)
        data_mismatch = res_mismatch.get_json()
        self.assertTrue(data_mismatch['error'] in ['session_conflict', 'Security violation: Zero-Trust Tab Guard mismatch.'])

        # 2. Matching header succeeds
        test_img2 = (io.BytesIO(b"fake_image_bytes"), "proof.jpg")
        res_match = self.client.post(
            f'/supervisor/issues/{self.ticket_prog_id}/verify-close',
            data={
                'technician_name': 'Vendor',
                'proof_image': test_img2,
                'resolution_notes': 'Inspected and working.'
            },
            content_type='multipart/form-data',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'X-Tab-Guard-ID': 'strict_server_guard_id_123'
            }
        )
        self.assertEqual(res_match.status_code, 200)

    def test_verify_and_close_enforces_at_least_supervisor_role(self):
        """User whose role is not at least SUPERVISOR must receive 403."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.faculty_id
            sess['user_role'] = User.ROLE_FACULTY
            sess['is_admin'] = False

        test_img = (io.BytesIO(b"fake_image_bytes"), "proof.jpg")
        res = self.client.post(
            f'/supervisor/issues/{self.ticket_open_id}/verify-close',
            data={
                'technician_name': 'Vendor',
                'proof_image': test_img,
                'resolution_notes': 'Hacked.'
            },
            content_type='multipart/form-data',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 403)

    def test_verify_and_close_requires_proof_image(self):
        """Submission without proof image returns 400 error."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True

        res = self.client.post(
            f'/supervisor/issues/{self.ticket_prog_id}/verify-close',
            data={
                'technician_name': 'External Plumber',
                'resolution_notes': 'Fixed tap.'
            },
            content_type='multipart/form-data',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('Proof of completion image is required', data['error'])

    def test_verify_and_close_compresses_image_with_pillow(self):
        """Image is opened via Pillow, converted to RGB, resized to max width 1200px, and compressed."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.supervisor_id
            sess['user_role'] = User.ROLE_SUPERVISOR
            sess['is_admin'] = True
            sess['tab_guard_id'] = 'pillow_guard_test_789'

        # Create a test high-resolution RGBA image: 1600x1200 (wider than 1200px)
        raw_img = Image.new('RGBA', (1600, 1200), color=(255, 100, 50, 200))
        img_buffer = io.BytesIO()
        raw_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        test_file = (img_buffer, "large_inspection_photo.png")

        res = self.client.post(
            f'/supervisor/issues/{self.ticket_prog_id}/verify-close',
            data={
                'technician_name': 'Santosh Vendor',
                'proof_image': test_file,
                'resolution_notes': 'Pipe replaced and water pressure verified at 3.5 bar.'
            },
            content_type='multipart/form-data',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'X-Tab-Guard-ID': 'pillow_guard_test_789'
            }
        )

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        with self.app.app_context():
            ticket = db.session.get(Ticket, self.ticket_prog_id)
            self.assertEqual(ticket.status, Ticket.STATUS_RESOLVED)
            self.assertEqual(ticket.verified_by_id, self.supervisor_id)
            self.assertTrue(ticket.completion_photo_filename.endswith('.webp'))

            # Check that compressed file exists on disk and verify dimensions
            upload_dir = os.path.join(self.app.root_path, 'static', 'uploads', 'proofs')
            saved_path = os.path.join(upload_dir, ticket.completion_photo_filename)
            self.assertTrue(os.path.exists(saved_path))

            with Image.open(saved_path) as saved_img:
                # Must be converted to RGB (no Alpha channel)
                self.assertEqual(saved_img.mode, 'RGB')
                # Must be resized to max width 1200px while maintaining aspect ratio (1600x1200 -> 1200x900)
                self.assertEqual(saved_img.width, 1200)
                self.assertEqual(saved_img.height, 900)

            # Check AuditLog committed in same transaction
            audit = AuditLog.query.filter_by(action="TICKET_VERIFIED_CLOSED", target_id=self.ticket_prog_id).first()
            self.assertIsNotNone(audit)
            self.assertEqual(audit.performed_by_id, self.supervisor_id)


if __name__ == '__main__':
    unittest.main()
