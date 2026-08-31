import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Floor, Room, Asset
from app.cache import invalidate_all_map_cache

def sync_ground_floor():
    f0 = Floor.query.filter_by(level=0).first()
    if not f0:
        print("Ground floor (Floor 0) not found!")
        return

    # Ground Floor Exact Definitions from VY0.svg
    f0_definitions = [
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
    ]

    # Delete stale rooms that don't exist in VY0.svg (e.g. placeholder VY024, VY026)
    valid_numbers = {d['number'] for d in f0_definitions}
    stale_rooms = Room.query.filter_by(floor_id=f0.id).filter(~Room.number.in_(valid_numbers)).all()
    for s in stale_rooms:
        print(f"Removing stale room on Ground floor: {s.number}")
        db.session.delete(s)
    db.session.flush()

    for defn in f0_definitions:
        room = Room.query.filter_by(floor_id=f0.id, number=defn['number']).first()
        if not room:
            room = Room(
                floor_id=f0.id,
                number=defn['number'],
                name=defn['name'],
                room_type=defn['type']
            )
            db.session.add(room)
            db.session.flush()
            print(f"Created {room.number} as {defn['type']}")
        else:
            room.name = defn['name']
            room.room_type = defn['type']
            print(f"Updated {room.number} to {defn['type']}")

        # Ensure assets exist
        if not room.assets:
            if room.room_type == Room.ROOM_TYPE_CLASSROOM:
                assets = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                ]
            elif room.room_type == Room.ROOM_TYPE_LAB:
                assets = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                    {'name': 'Computer Workstations', 'type': 'computer'},
                ]
            elif room.room_type == Room.ROOM_TYPE_CONFERENCE:
                assets = [
                    {'name': 'Conference Table', 'type': 'table'},
                    {'name': 'Presentation Display', 'type': 'display'},
                    {'name': 'Video Conferencing Kit', 'type': 'camera'},
                    {'name': 'AC Unit', 'type': 'ac'},
                ]
            elif room.room_type == 'faculty':
                assets = [
                    {'name': 'Desks & Chairs', 'type': 'furniture'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                ]
            else:
                assets = [
                    {'name': 'Lights', 'type': 'light'},
                    {'name': 'Exhaust Fan', 'type': 'fan'},
                ]
            for a in assets:
                db.session.add(Asset(
                    room_id=room.id,
                    name=a['name'],
                    asset_type=a['type'],
                    status=Asset.STATUS_WORKING,
                    installation_date=datetime.now() - timedelta(days=random.randint(0, 365*3))
                ))

    db.session.commit()
    invalidate_all_map_cache()
    print("Ground Floor sync successfully completed and cache cleared!")

def sync_floor_1():
    f1 = Floor.query.filter_by(level=1).first()
    if not f1:
        print("Floor 1 not found!")
        return

    # Floor 1 Exact Definitions from VY1.svg
    f1_definitions = [
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
    ]

    valid_numbers = {d['number'] for d in f1_definitions}
    stale_rooms = Room.query.filter_by(floor_id=f1.id).filter(~Room.number.in_(valid_numbers)).all()
    for s in stale_rooms:
        print(f"Removing stale room on Floor 1: {s.number}")
        db.session.delete(s)
    db.session.flush()

    for defn in f1_definitions:
        room = Room.query.filter_by(floor_id=f1.id, number=defn['number']).first()
        if not room:
            room = Room(
                floor_id=f1.id,
                number=defn['number'],
                name=defn['name'],
                room_type=defn['type']
            )
            db.session.add(room)
            db.session.flush()
            print(f"Created {room.number} as {defn['type']}")
        else:
            room.name = defn['name']
            room.room_type = defn['type']
            print(f"Updated {room.number} to {defn['type']}")

        if not room.assets:
            if room.room_type == Room.ROOM_TYPE_CLASSROOM:
                assets = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                ]
            elif room.room_type == Room.ROOM_TYPE_LAB:
                assets = [
                    {'name': 'Projector', 'type': 'projector'},
                    {'name': 'Whiteboard', 'type': 'whiteboard'},
                    {'name': 'AC Unit', 'type': 'ac'},
                    {'name': 'Ceiling Lights', 'type': 'light'},
                    {'name': 'Computer Workstations', 'type': 'computer'},
                ]
            else:
                assets = [
                    {'name': 'Lights', 'type': 'light'},
                    {'name': 'Exhaust Fan', 'type': 'fan'},
                ]
            for a in assets:
                db.session.add(Asset(
                    room_id=room.id,
                    name=a['name'],
                    asset_type=a['type'],
                    status=Asset.STATUS_WORKING,
                    installation_date=datetime.now() - timedelta(days=random.randint(0, 365*3))
                ))

    db.session.commit()
    invalidate_all_map_cache()
    print("Floor 1 sync successfully completed and cache cleared!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        sync_ground_floor()
        sync_floor_1()
