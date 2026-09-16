import os
os.environ['TESTING'] = 'True'

import unittest
from datetime import time
from app import create_app, db
from app.models import User, Building, Floor, Room, Timetable

class TestBulkAssignFaculty(unittest.TestCase):
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
            b = Building(name="Vyas", description="Vyas Building")
            db.session.add(b)
            db.session.flush()

            f = Floor(building_id=b.id, level=3, name="3rd Floor")
            db.session.add(f)
            db.session.flush()

            r = Room(floor_id=f.id, number="VY301", name="Classroom 301")
            db.session.add(r)
            db.session.flush()

            self.admin = User(name="Admin User", email="admin.cmm@mitwpu.edu.in", role=User.ROLE_ADMIN, is_admin=True)
            self.admin.set_password("adminpass")

            self.faculty = User(name="Dr. Alan Turing", email="turing@mitwpu.edu.in", role=User.ROLE_FACULTY, is_admin=False)
            self.faculty.set_password("facultypass")

            db.session.add_all([self.admin, self.faculty])
            db.session.commit()

            self.admin_id = self.admin.id
            self.faculty_id = self.faculty.id

            # Create 3 unassigned timetable slots
            tt1 = Timetable(room_id=r.id, day_of_week=0, start_time=time(9, 0), end_time=time(10, 0), subject="Data Structures", course="SYBCA", division="Div A")
            tt2 = Timetable(room_id=r.id, day_of_week=1, start_time=time(10, 0), end_time=time(11, 0), subject="Python Programming", course="SYBCA", division="Div A")
            tt3 = Timetable(room_id=r.id, day_of_week=2, start_time=time(11, 0), end_time=time(12, 0), subject="Operating Systems", course="SYBCA", division="Div A")
            db.session.add_all([tt1, tt2, tt3])
            db.session.commit()

            self.tt1_id = tt1.id
            self.tt2_id = tt2.id
            self.tt3_id = tt3.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_bulk_assign_success(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['is_admin'] = True
            sess['user_role'] = User.ROLE_ADMIN

        payload = {
            "faculty_id": self.faculty_id,
            "class_ids": [self.tt1_id, self.tt2_id, self.tt3_id]
        }

        resp = self.client.post(
            '/admin/api/bulk_assign_faculty',
            json=payload,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['updated_count'], 3)
        self.assertEqual(data['data']['faculty_id'], self.faculty_id)

        # Verify DB records updated
        with self.app.app_context():
            classes = Timetable.query.filter(Timetable.id.in_([self.tt1_id, self.tt2_id, self.tt3_id])).all()
            for cls in classes:
                self.assertEqual(cls.faculty_id, self.faculty_id)

    def test_bulk_assign_validation_errors(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['is_admin'] = True
            sess['user_role'] = User.ROLE_ADMIN

        # Missing faculty_id
        resp = self.client.post('/admin/api/bulk_assign_faculty', json={"class_ids": [self.tt1_id]})
        self.assertEqual(resp.status_code, 400)

        # Empty class_ids
        resp = self.client.post('/admin/api/bulk_assign_faculty', json={"faculty_id": self.faculty_id, "class_ids": []})
        self.assertEqual(resp.status_code, 400)

        # Nonexistent faculty
        resp = self.client.post('/admin/api/bulk_assign_faculty', json={"faculty_id": 99999, "class_ids": [self.tt1_id]})
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
