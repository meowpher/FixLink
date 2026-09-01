import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Floor, Room, Asset
from app.cache import invalidate_all_map_cache

FLOOR_DEFINITIONS = {
    0: [
        # Classrooms (Blue)
        {'number': 'VY002', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 002'},
        {'number': 'VY003', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 003'},
        {'number': 'VY004', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 004'},
        {'number': 'VY015', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 015'},
        {'number': 'VY016', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 016'},

        # Labs (Teal)
        {'number': 'VY007', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 007'},
        {'number': 'VY014', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 014'},
        {'number': 'VY027', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 027'},
        {'number': 'VY028', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 028'},
        {'number': 'VY029', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 029'},
        {'number': 'VY030', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 030'},

        # Faculty Areas (Orange/Yellow)
        {'number': 'VY025A', 'type': 'faculty', 'name': 'Faculty Area 025A'},
        {'number': 'VY025B', 'type': 'faculty', 'name': 'Faculty Area 025B'},
        {'number': 'VY025C', 'type': 'faculty', 'name': 'Faculty Area 025C'},

        # Conference Rooms (Purple)
        {'number': 'VY001', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 001'},
        {'number': 'VY025D', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 025D'},
        {'number': 'VY025E', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 025E'},

        # Washrooms (Red)
        {'number': 'VY008', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 008'},
        {'number': 'VY009', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 009'},
        {'number': 'VY010', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 010'},
        {'number': 'VY011', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 011'},
        {'number': 'VY017', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 017'},
        {'number': 'VY018', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 018'},
        {'number': 'VY019', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 019'},
        {'number': 'VY020', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 020'},
        {'number': 'VY021', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 021'},

        # Lifts
        {'number': 'VY0Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY0Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY0Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY0Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY0Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY0Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY0Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY0Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    1: [
        # Classrooms (Blue)
        {'number': 'VY101', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 101'},
        {'number': 'VY102', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 102'},
        {'number': 'VY103', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 103'},
        {'number': 'VY104', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 104'},
        {'number': 'VY114', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 114'},
        {'number': 'VY115', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 115'},
        {'number': 'VY124', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 124'},
        
        # Labs (Teal)
        {'number': 'VY112', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 112'},
        {'number': 'VY113', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 113'},
        {'number': 'VY123', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 123'},
        {'number': 'VY126', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 126'},
        {'number': 'VY127', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 127'},
        {'number': 'VY128', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 128'},
        {'number': 'VY129', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 129'},
        
        # Washrooms (Red)
        {'number': 'VY110', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 110'},
        {'number': 'VY111', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 111'},
        {'number': 'VY116', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 116'},
        {'number': 'VY117', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 117'},
        {'number': 'VY118', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 118'},
        {'number': 'VY119', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 119'},
        {'number': 'VY120', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 120'},
        
        # Lifts
        {'number': 'VY1Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY1Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY1Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY1Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY1Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY1Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY1Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY1Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    2: [
        # Classrooms (Blue)
        {'number': 'VY201', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 201'},
        {'number': 'VY202', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 202'},
        {'number': 'VY203', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 203'},
        {'number': 'VY204', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 204'},
        {'number': 'VY206', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 206'},
        {'number': 'VY213', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 213'},
        {'number': 'VY214', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 214'},
        {'number': 'VY223', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 223'},

        # Labs (Teal)
        {'number': 'VY212', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 212'},
        {'number': 'VY222', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 222'},
        {'number': 'VY225', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 225'},
        {'number': 'VY226', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 226'},
        {'number': 'VY227', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 227'},
        {'number': 'VY228', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 228'},

        # Washrooms (Red)
        {'number': 'VY209', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 209'},
        {'number': 'VY210', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 210'},
        {'number': 'VY215', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 215'},
        {'number': 'VY216', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 216'},
        {'number': 'VY217', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 217'},
        {'number': 'VY218', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 218'},
        {'number': 'VY219', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 219'},

        # Lifts
        {'number': 'VY2Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY2Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY2Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY2Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY2Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY2Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY2Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY2Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    3: [
        # Faculty
        {'number': 'VY307', 'type': 'faculty', 'name': 'Faculty Area 307'},

        # Classrooms (Blue)
        {'number': 'VY301', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 301'},
        {'number': 'VY302', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 302'},
        {'number': 'VY303', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 303'},
        {'number': 'VY304', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 304'},
        {'number': 'VY315', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 315'},
        {'number': 'VY316', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 316'},
        {'number': 'VY325', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 325'},

        # Labs (Teal)
        {'number': 'VY314', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 314'},
        {'number': 'VY326', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 326'},
        {'number': 'VY327', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 327'},
        {'number': 'VY328', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 328'},
        {'number': 'VY329', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 329'},
        {'number': 'VY330', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 330'},

        # Washrooms (Red)
        {'number': 'VY311', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 311'},
        {'number': 'VY312', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 312'},
        {'number': 'VY317', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 317'},
        {'number': 'VY318', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 318'},
        {'number': 'VY319', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 319'},
        {'number': 'VY320', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 320'},
        {'number': 'VY321', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 321'},

        # Lifts
        {'number': 'VY3Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY3Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY3Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY3Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY3Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY3Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY3Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY3Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    4: [
        # Classrooms (Blue)
        {'number': 'VY401', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 401'},
        {'number': 'VY402', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 402'},
        {'number': 'VY403', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 403'},
        {'number': 'VY404', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 404'},
        {'number': 'VY413', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 413'},
        {'number': 'VY414', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 414'},
        {'number': 'VY424', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 424'},

        # Labs (Teal)
        {'number': 'VY406', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 406'},
        {'number': 'VY412', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 412'},
        {'number': 'VY422', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 422'},
        {'number': 'VY426', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 426'},
        {'number': 'VY427', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 427'},
        {'number': 'VY428', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 428'},
        {'number': 'VY429', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 429'},

        # Washrooms (Red)
        {'number': 'VY407', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 407'},
        {'number': 'VY408', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 408'},
        {'number': 'VY415', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 415'},
        {'number': 'VY416', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 416'},
        {'number': 'VY417', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 417'},
        {'number': 'VY418', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 418'},
        {'number': 'VY419', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 419'},

        # Lifts
        {'number': 'VY4Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY4Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY4Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY4Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY4Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY4Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY4Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY4Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    5: [
        # Canteen
        {'number': 'ENCAVE', 'type': 'canteen', 'name': 'Encave Canteen'},

        # Faculty
        {'number': 'VY523', 'type': 'faculty', 'name': 'Faculty Area 523'},

        # Classrooms (Blue)
        {'number': 'VY501', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 501'},
        {'number': 'VY502', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 502'},
        {'number': 'VY503', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 503'},
        {'number': 'VY504', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 504'},
        {'number': 'VY514', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 514'},
        {'number': 'VY515', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 515'},
        {'number': 'VY524', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 524'},

        # Labs (Teal)
        {'number': 'VY512', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 512'},
        {'number': 'VY513', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 513'},
        {'number': 'VY526', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 526'},
        {'number': 'VY527', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 527'},
        {'number': 'VY528', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 528'},
        {'number': 'VY529', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 529'},

        # Washrooms (Red)
        {'number': 'VY508', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 508'},
        {'number': 'VY509', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 509'},
        {'number': 'VY516', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 516'},
        {'number': 'VY517', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 517'},
        {'number': 'VY518', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 518'},
        {'number': 'VY519', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 519'},
        {'number': 'VY520', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 520'},

        # Lifts
        {'number': 'VY5Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY5Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY5Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY5Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY5Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY5Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY5Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY5Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    6: [
        # Meeting Rooms
        {'number': 'MR4', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 4'},
        {'number': 'MR5', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 5'},
        {'number': 'MR6', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 6'},
        {'number': 'MR7', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 7'},
        {'number': 'MR8', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 8'},
        {'number': 'MR11', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 11'},
        {'number': 'MR12', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 12'},
        {'number': 'MR13', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 13'},
        {'number': 'MR14', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 14'},
        {'number': 'MR15', 'type': Room.ROOM_TYPE_MEETING, 'name': 'Meeting Room 15'},

        # Unavailable Meeting Rooms (Shown on Map)
        {'number': 'MR1', 'type': 'unavailable', 'name': 'Meeting Room 1'},
        {'number': 'MR2', 'type': 'unavailable', 'name': 'Meeting Room 2'},
        {'number': 'MR3', 'type': 'unavailable', 'name': 'Meeting Room 3'},
        {'number': 'MR9', 'type': 'unavailable', 'name': 'Meeting Room 9'},
        {'number': 'MR10', 'type': 'unavailable', 'name': 'Meeting Room 10'},

        # Conference Rooms
        {'number': 'VY602', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 602'},
        {'number': 'VY610', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 610'},
        {'number': 'VY613', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 613'},

        # Washrooms
        {'number': 'VY608', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 608'},
        {'number': 'VY609', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 609'},
        {'number': 'VY614', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 614'},
        {'number': 'VY615', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 615'},
        {'number': 'VY616', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 616'},

        # Lifts
        {'number': 'VY6Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY6Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY6Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY6Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY6Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY6Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY6Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY6Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ],
    7: [
        # Faculty
        {'number': 'VY707', 'type': 'faculty', 'name': 'Faculty Room 707'},

        # Kitchens
        {'number': 'VY706', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Main Kitchen 706'},
        {'number': 'VY712', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Pastry Kitchen 712'},
        {'number': 'VY713', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Kitchen 713'},
        {'number': 'VY714', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Kitchen 714'},
        {'number': 'VY715', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Prep Kitchen 715'},

        # Lab
        {'number': 'VY726', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 726'},

        # Classrooms
        {'number': 'VY701', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 701'},
        {'number': 'VY702', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 702'},
        {'number': 'VY703', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 703'},
        {'number': 'VY704', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 704'},
        {'number': 'VY716', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 716'},
        {'number': 'VY717', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 717'},
        {'number': 'VY718', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 718'},
        {'number': 'VY727', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 727'},
        {'number': 'VY728', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 728'},
        {'number': 'VY729', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 729'},
        {'number': 'VY730', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 730'},

        # Washrooms
        {'number': 'VY709', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 709'},
        {'number': 'VY710', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 710'},
        {'number': 'VY719', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 719'},
        {'number': 'VY720', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 720'},
        {'number': 'VY721', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 721'},
        {'number': 'VY722', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 722'},

        # Lifts
        {'number': 'VY7Lift1', 'type': 'lift', 'name': 'Lift 1'},
        {'number': 'VY7Lift2', 'type': 'lift', 'name': 'Lift 2'},
        {'number': 'VY7Lift3', 'type': 'lift', 'name': 'Lift 3'},
        {'number': 'VY7Lift4', 'type': 'lift', 'name': 'Lift 4'},
        {'number': 'VY7Lift5', 'type': 'lift', 'name': 'Lift 5'},
        {'number': 'VY7Lift6', 'type': 'lift', 'name': 'Lift 6'},
        {'number': 'VY7Lift7', 'type': 'lift', 'name': 'Lift 7'},
        {'number': 'VY7Lift8', 'type': 'lift', 'name': 'Lift 8'},
    ]
}

def sync_single_floor(level, definitions):
    floor = Floor.query.filter_by(level=level).first()
    if not floor:
        print(f"Floor {level} not found in DB!")
        return

    valid_numbers = {d['number'] for d in definitions}
    stale_rooms = Room.query.filter_by(floor_id=floor.id).filter(~Room.number.in_(valid_numbers)).all()
    for s in stale_rooms:
        print(f"Removing stale room on Floor {level}: {s.number}")
        # Delete associated assets first
        Asset.query.filter_by(room_id=s.id).delete()
        db.session.delete(s)
    db.session.commit()

    existing_rooms = {r.number: r for r in Room.query.filter_by(floor_id=floor.id).all()}
    
    for defn in definitions:
        room = existing_rooms.get(defn['number'])
        if not room:
            room = Room(
                floor_id=floor.id,
                number=defn['number'],
                name=defn['name'],
                room_type=defn['type']
            )
            db.session.add(room)
            db.session.flush()
            print(f"Floor {level}: Created {room.number} ({defn['type']})")
        else:
            room.name = defn['name']
            room.room_type = defn['type']
            print(f"Floor {level}: Updated {room.number} ({defn['type']})")

    db.session.commit()

    # Bulk add missing assets for rooms on this floor
    rooms = Room.query.filter_by(floor_id=floor.id).all()
    existing_asset_room_ids = {row[0] for row in db.session.query(Asset.room_id).filter(Asset.room_id.in_([r.id for r in rooms])).distinct().all()}

    new_assets = []
    for room in rooms:
        if room.id not in existing_asset_room_ids:
            if room.room_type == Room.ROOM_TYPE_CLASSROOM:
                asset_defs = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                ]
            elif room.room_type == Room.ROOM_TYPE_LAB:
                asset_defs = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                    {'name': 'Computer Workstations', 'type': 'computer'},
                ]
            elif room.room_type in [Room.ROOM_TYPE_CONFERENCE, Room.ROOM_TYPE_MEETING]:
                asset_defs = [
                    {'name': 'Conference Table', 'type': 'table'},
                    {'name': 'Presentation Display', 'type': 'display'},
                    {'name': 'Video Conferencing Kit', 'type': 'camera'},
                    {'name': 'AC Unit', 'type': 'ac'},
                ]
            elif room.room_type == Room.ROOM_TYPE_KITCHEN:
                asset_defs = [
                    {'name': 'Commercial Stove', 'type': 'stove'},
                    {'name': 'Industrial Exhaust System', 'type': 'exhaust'},
                    {'name': 'Walk-in Refrigerator', 'type': 'fridge'},
                    {'name': 'Prep Stations', 'type': 'prep_station'},
                    {'name': 'Industrial Oven', 'type': 'oven'},
                    {'name': 'Fire Extinguisher', 'type': 'safety'},
                ]
            elif room.room_type == 'canteen':
                asset_defs = [
                    {'name': 'Serving Counter', 'type': 'counter'},
                    {'name': 'Dining Tables', 'type': 'table'},
                    {'name': 'Beverage Cooler', 'type': 'cooler'},
                    {'name': 'Exhaust System', 'type': 'exhaust'},
                ]
            elif room.room_type == 'faculty':
                asset_defs = [
                    {'name': 'Desks & Chairs', 'type': 'furniture'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                ]
            else:
                asset_defs = [
                    {'name': 'Lights', 'type': 'light'},
                    {'name': 'Exhaust Fan', 'type': 'fan'},
                ]

            for a in asset_defs:
                new_assets.append(Asset(
                    room_id=room.id,
                    name=a['name'],
                    asset_type=a['type'],
                    status=Asset.STATUS_WORKING,
                    installation_date=datetime.now() - timedelta(days=random.randint(0, 365*3))
                ))

    if new_assets:
        db.session.bulk_save_objects(new_assets)
        db.session.commit()

    print(f"Floor {level} successfully synchronized!")

def sync_all_floors():
    for level, definitions in FLOOR_DEFINITIONS.items():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sync_single_floor(level, definitions)
                break
            except Exception as e:
                db.session.rollback()
                print(f"Attempt {attempt + 1} for Floor {level} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    invalidate_all_map_cache()
    print("All floors synchronized and map cache invalidated successfully!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        sync_all_floors()
