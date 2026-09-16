import unittest
from app.blueprints.faculty.routes import parse_timetable_subject_metadata

class TestTimetableSubjectSanitizer(unittest.TestCase):
    def test_sybca_div_a_ds(self):
        res = parse_timetable_subject_metadata("SYBCA DIV-A DS")
        self.assertEqual(res['course'], "SYBCA")
        self.assertEqual(res['division'], "Div A")
        self.assertEqual(res['subject'], "Data Structures (DS)")

    def test_symca_div_e_with_time(self):
        res = parse_timetable_subject_metadata("SYMCA DIV E (11.00-12.00)")
        self.assertEqual(res['course'], "SYMCA")
        self.assertEqual(res['division'], "Div E")
        self.assertEqual(res['subject'], "General Lecture")

    def test_sybca_div_b_python(self):
        res = parse_timetable_subject_metadata("SYBCA DIV-B Python")
        self.assertEqual(res['course'], "SYBCA")
        self.assertEqual(res['division'], "Div B")
        self.assertEqual(res['subject'], "Python Programming")

    def test_sybca_div_c_python(self):
        res = parse_timetable_subject_metadata("SYBCA DIV-C Python")
        self.assertEqual(res['course'], "SYBCA")
        self.assertEqual(res['division'], "Div C")
        self.assertEqual(res['subject'], "Python Programming")

    def test_sybsc_div_a(self):
        res = parse_timetable_subject_metadata("SYBSC DIV A")
        self.assertEqual(res['course'], "SYBSC")
        self.assertEqual(res['division'], "Div A")
        self.assertEqual(res['subject'], "General Lecture")

    def test_sybsc_div_b_cpp(self):
        res = parse_timetable_subject_metadata("SYBSC-Div B C++")
        self.assertEqual(res['course'], "SYBSC")
        self.assertEqual(res['division'], "Div B")
        self.assertEqual(res['subject'], "C++ Programming")

    def test_fymca_div_a(self):
        res = parse_timetable_subject_metadata("FYMCA Div A")
        self.assertEqual(res['course'], "FYMCA")
        self.assertEqual(res['division'], "Div A")
        self.assertEqual(res['subject'], "General Lecture")

    def test_bsc_cs_honors_with_time(self):
        res = parse_timetable_subject_metadata("BSC CS HONORS 9.00-12.00")
        self.assertEqual(res['course'], "BSc CS Honours")
        self.assertIsNone(res['division'])
        self.assertEqual(res['subject'], "General Lecture")

    def test_bca_hons(self):
        res = parse_timetable_subject_metadata("BCA HONS")
        self.assertEqual(res['course'], "BCA Honours")
        self.assertIsNone(res['division'])
        self.assertEqual(res['subject'], "General Lecture")

    def test_regular_subject_only(self):
        res = parse_timetable_subject_metadata("Operating Systems")
        self.assertIsNone(res['course'])
        self.assertIsNone(res['division'])
        self.assertEqual(res['subject'], "Operating Systems")

    def test_complex_div_and_subject(self):
        res = parse_timetable_subject_metadata("TYBCA Div C Database Management Systems")
        self.assertEqual(res['course'], "TYBCA")
        self.assertEqual(res['division'], "Div C")
        self.assertEqual(res['subject'], "Database Management Systems")

if __name__ == '__main__':
    unittest.main()
