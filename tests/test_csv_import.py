import os
os.environ['TESTING'] = 'True'

import io
import unittest
from app import create_app, db
from app.models import User, Building, Floor, Room, Timetable
from app.blueprints.faculty.routes import parse_timetable_csv

class TestCSVTimetableImport(unittest.TestCase):
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
            
            f = Floor(building_id=b.id, level=4, name="4th Floor")
            db.session.add(f)
            db.session.flush()
            
            r1 = Room(floor_id=f.id, number="VY401", name="Classroom 401")
            r2 = Room(floor_id=f.id, number="VY404", name="Programming Lab 404")
            db.session.add_all([r1, r2])
            
            fac = User(name="Prof. Sharma", email="sharma@mitwpu.edu.in", role=User.ROLE_FACULTY, is_admin=False)
            fac.set_password("password123")
            
            admin = User(name="Admin User", email="admin@mitwpu.edu.in", role=User.ROLE_ADMIN, is_admin=True)
            admin.set_password("password123")
            
            db.session.add_all([fac, admin])
            db.session.commit()
            
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_parse_matrix_csv(self):
        csv_data = (
            "Room No,Time,Mon,Tue,Wed,Thu,Fri\n"
            "VY401,10:00 - 11:00,Data Structures,Operating Systems,,,Physics Lab\n"
            "VY404,11:00 - 12:00,Computer Networks,AI & ML,,,\n"
        ).encode('utf-8')
        
        with self.app.app_context():
            entries, errors = parse_timetable_csv(csv_data)
            self.assertEqual(len(errors), 0)
            self.assertGreater(len(entries), 0)
            
            first = entries[0]
            self.assertEqual(first['room_number'], 'VY401')
            self.assertEqual(first['start_time'], '10:00')
            self.assertEqual(first['day_name'], 'Monday')
            self.assertEqual(first['subject'], 'Data Structures')

    def test_parse_matrix_csv_with_raw_room_numbers(self):
        csv_data = (
            "Classroom,Time Slot,Monday,Tuesday\n"
            "404,09:00 - 10:00,Database Systems,Python Programming\n"
        ).encode('utf-8')
        
        with self.app.app_context():
            entries, errors = parse_timetable_csv(csv_data)
            self.assertEqual(len(errors), 0)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]['room_number'], 'VY404')
            self.assertEqual(entries[0]['subject'], 'Database Systems')

    def test_faculty_user_denied_mass_csv_import(self):
        with self.client:
            with self.app.app_context():
                fac = User.query.filter_by(email="sharma@mitwpu.edu.in").first()
                fac_id = fac.id
            
            with self.client.session_transaction() as sess:
                sess['user_id'] = fac_id
                sess['user_role'] = User.ROLE_FACULTY
                sess['is_admin'] = False
            
            csv_bytes = ("Room No,Time,Mon\nVY401,09:00 - 10:00,Software Engineering\n").encode('utf-8')
            
            res = self.client.post(
                '/faculty/api/timetable/preview-csv',
                data={'csvFile': (io.BytesIO(csv_bytes), 'timetable.csv')},
                content_type='multipart/form-data'
            )
            data = res.get_json()
            self.assertFalse(data['success'])
            self.assertEqual(res.status_code, 403)

    def test_admin_mass_import_and_scoped_deletion(self):
        with self.client:
            with self.app.app_context():
                admin = User.query.filter_by(email="admin@mitwpu.edu.in").first()
                admin_id = admin.id
                r1 = Room.query.filter_by(number="VY401").first()
                r2 = Room.query.filter_by(number="VY404").first()
                f = Floor.query.filter_by(level=4).first()
                r1_id, r2_id, f_id = r1.id, r2.id, f.id
            
            with self.client.session_transaction() as sess:
                sess['user_id'] = admin_id
                sess['user_role'] = User.ROLE_ADMIN
                sess['is_admin'] = True
            
            csv_bytes = (
                "Room No,Time,Mon,Tue\n"
                "VY401,09:00 - 10:00,Software Engineering,Cloud Computing\n"
                "VY404,10:00 - 11:00,AI Systems,Machine Learning\n"
            ).encode('utf-8')
            
            # Preview
            res = self.client.post(
                '/faculty/api/timetable/preview-csv',
                data={'csvFile': (io.BytesIO(csv_bytes), 'timetable.csv')},
                content_type='multipart/form-data'
            )
            data = res.get_json()
            self.assertTrue(data['success'])
            parsed_entries = data['data']['parsed_entries']
            self.assertEqual(len(parsed_entries), 4)
            
            # Commit
            res_commit = self.client.post('/faculty/api/timetable/import-csv', json={'entries': parsed_entries})
            self.assertTrue(res_commit.get_json()['success'])
            
            with self.app.app_context():
                self.assertEqual(Timetable.query.count(), 4)
            
            # Delete Room Scope (VY401)
            res_del_room = self.client.post('/admin/api/timetable/delete', json={'scope': 'room', 'room_id': r1_id})
            self.assertTrue(res_del_room.get_json()['success'])
            with self.app.app_context():
                self.assertEqual(Timetable.query.filter_by(room_id=r1_id).count(), 0)
                self.assertEqual(Timetable.query.filter_by(room_id=r2_id).count(), 2)

            # Delete Floor Scope (4th Floor)
            res_del_floor = self.client.post('/admin/api/timetable/delete', json={'scope': 'floor', 'floor_id': f_id})
            self.assertTrue(res_del_floor.get_json()['success'])
            with self.app.app_context():
                self.assertEqual(Timetable.query.count(), 0)

if __name__ == '__main__':
    unittest.main()
