#!/usr/bin/env python3
"""
MIT-WPU Vyas Smart-Room Maintenance Tracker
Database Initialization Script

This script creates the Vyas building with:
- 8 Floors (Ground [0] to 7th Floor)
- 4th Floor with detailed layout matching the floor plan image
- Generic rooms for other floors
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Building, Floor, Room, Asset, Ticket

def create_vyas_data(app=None):
    """Create Vyas building with floors and rooms."""
    if app is None:
        app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MIT-WPU Vyas Tracker - Database Initialization")
        print("=" * 60)
        
        # Check if data already exists
        existing = Building.query.filter_by(name='Vyas').first()
        if existing:
            print(f"\n  Vyas building already exists.")
            response = input("Do you want to reset and recreate all data? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
            
            # Clear existing data
            print("\n  Clearing existing data...")
            Ticket.query.delete()
            Asset.query.delete()
            Room.query.delete()
            Floor.query.delete()
            Building.query.delete()
            db.session.commit()
            print(" Existing data cleared.")
        
        # Create Vyas Building
        print("\n Creating Vyas Building...")
        vyas = Building(
            name='Vyas',
            description='Academic building with classrooms and laboratories'
        )
        db.session.add(vyas)
        db.session.commit()
        print(f"   Created: {vyas.name}")
        

        # Create 8 Floors (Ground to 7th)
        print("\n Creating Floors...")
        floors = []
        floor_names = [
            'Ground Floor',
            '1st Floor',
            '2nd Floor',
            '3rd Floor',
            '4th Floor',
            '5th Floor',
            '6th Floor',
            '7th Floor'
        ]
        
        for level, name in enumerate(floor_names):
            floor = Floor(
                building_id=vyas.id,
                level=level,
                name=name
            )
            db.session.add(floor)
            floors.append(floor)
            print(f"   Created: {name}")
        
        db.session.commit()
        
        # Create rooms for each floor
        print("\n Creating Rooms...")
        
        # Define floors that should have the detailed layout
        detailed_floors = [2, 4, 5]
        
        for floor in floors:
            print(f"\n   Creating rooms for {floor.name}...")
            
            if floor.level == 3:
                # 3RD FLOOR (Pilot SVG Layout)
                third_floor_rooms = [
                    # Classrooms (Blue)
                    {'suffix': '16', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 316'},
                    {'suffix': '01', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 301'},
                    {'suffix': '25', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 325'},
                    {'suffix': '03', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 303'},
                    {'suffix': '04', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 304'},
                    {'suffix': '15', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 315'},
                    {'suffix': '02', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Classroom 302'},
                    
                    # Labs (Teal)
                    {'suffix': '26', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 326'},
                    {'suffix': '30', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 330'},
                    {'suffix': '29', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 329'},
                    {'suffix': '28', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 328'},
                    {'suffix': '27', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 327'},
                    {'suffix': '14', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab 314'},
                    
                    # Washrooms (Red)
                    {'suffix': '12', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 312'},
                    {'suffix': '18', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 318'},
                    {'suffix': '20', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 320'},
                    {'suffix': '19', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 319'},
                    {'suffix': '17', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 317'},
                    {'suffix': '21', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 321'},
                    {'suffix': '11', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 311'},
                    
                    # Faculty (Yellow)
                    {'suffix': '07', 'type': 'faculty', 'name': 'Faculty Area 307'},
                    
                    # Lifts
                    {'suffix': 'Lift1', 'type': 'lift', 'name': 'Lift 1'},
                    {'suffix': 'Lift2', 'type': 'lift', 'name': 'Lift 2'},
                    {'suffix': 'Lift3', 'type': 'lift', 'name': 'Lift 3'},
                    {'suffix': 'Lift4', 'type': 'lift', 'name': 'Lift 4'},
                    {'suffix': 'Lift5', 'type': 'lift', 'name': 'Lift 5'},
                    {'suffix': 'Lift6', 'type': 'lift', 'name': 'Lift 6'},
                    {'suffix': 'Lift7', 'type': 'lift', 'name': 'Lift 7'},
                    {'suffix': 'Lift8', 'type': 'lift', 'name': 'Lift 8'},
                ]
                
                for tmpl in third_floor_rooms:
                    room_number = f"VY3{tmpl['suffix']}" if tmpl['type'] != 'lift' else f"VY3{tmpl['suffix']}"
                    # Keep Lift names like VY3Lift1 to match existing convention
                    
                    room = Room(
                        floor_id=floor.id,
                        number=room_number,
                        name=tmpl['name'],
                        room_type=tmpl['type']
                    )
                    db.session.add(room)
                    print(f"     Created: {room_number} - {tmpl['name']}")

            elif floor.level == 1:
                # 1ST FLOOR (Matching VY1.svg)
                first_floor_rooms = [
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
                for tmpl in first_floor_rooms:
                    room = Room(floor_id=floor.id, number=tmpl['number'], name=tmpl['name'], room_type=tmpl['type'])
                    db.session.add(room)
                    print(f"     Created: {tmpl['number']} - {tmpl['name']}")
                    
            elif floor.level in detailed_floors:
                # DETAILED LAYOUT (Same as 4th Floor)
                level_digit = str(floor.level)
                
                # Room Templates (using placeholders X for level)
                # We'll replace 'VY4' with 'VY{level}' and '401' with '{level}01'
                room_templates = [
                    # Left Column (Classrooms - Blue)
                    {'suffix': '01', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '01'},
                    {'suffix': '02', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '02'},
                    {'suffix': '03', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '03'},
                    {'suffix': '04', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '04'},
                    
                    # Center Column (Labs - Teal)
                    {'suffix': '26', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab'},
                    {'suffix': '27', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab'},
                    {'suffix': '28', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab'},
                    {'suffix': '29', 'type': Room.ROOM_TYPE_LAB, 'name': 'Computer Lab'},
                    
                    # Top/Right Section
                    {'suffix': '24', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': 'Large Classroom'},
                    {'suffix': '22', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab'},
                    
                    # Right Column (Classrooms - Blue)
                    {'suffix': '14', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '14'},
                    {'suffix': '13', 'type': Room.ROOM_TYPE_CLASSROOM, 'name_suffix': '13'},
                    
                    # Right Edge (Washrooms/Staff - Red)
                    {'suffix': '19', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Staff/Storage'},
                    {'suffix': '18', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Staff/Storage'},
                    {'suffix': '17', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Staff/Storage'},
                    {'suffix': '16', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom'},
                    {'suffix': '15', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom'},
                    {'suffix': '08', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom'},
                    {'suffix': '07', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom'},
                    
                    # Lifts (8)
                    {'suffix': 'Lift1', 'type': 'lift', 'name': 'Lift 1'},
                    {'suffix': 'Lift2', 'type': 'lift', 'name': 'Lift 2'},
                    {'suffix': 'Lift3', 'type': 'lift', 'name': 'Lift 3'},
                    {'suffix': 'Lift4', 'type': 'lift', 'name': 'Lift 4'},
                    {'suffix': 'Lift5', 'type': 'lift', 'name': 'Lift 5'},
                    {'suffix': 'Lift6', 'type': 'lift', 'name': 'Lift 6'},
                    {'suffix': 'Lift7', 'type': 'lift', 'name': 'Lift 7'},
                    {'suffix': 'Lift8', 'type': 'lift', 'name': 'Lift 8'},
                ]
                
                for tmpl in room_templates:
                    room_number = f"VY{level_digit}{tmpl['suffix']}"
                    
                    if 'name_suffix' in tmpl:
                        room_name = f"Classroom {level_digit}{tmpl['name_suffix']}"
                    elif 'name' in tmpl:
                         # e.g., "Computer Lab 426" -> "Computer Lab {level}26"
                         room_name = f"{tmpl['name']} {level_digit}{tmpl['suffix']}"
                    
                    room = Room(
                        floor_id=floor.id,
                        number=room_number,
                        name=room_name,
                        room_type=tmpl['type']
                    )
                    db.session.add(room)
                    print(f"     Created: {room_number} - {room_name}")

            elif floor.level == 0:
                # GROUND FLOOR (Exact Layout from VY0.svg)
                gf_rooms = [
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

                    # Lifts (8)
                    {'number': 'VY0Lift1', 'type': 'lift', 'name': 'Lift 1'},
                    {'number': 'VY0Lift2', 'type': 'lift', 'name': 'Lift 2'},
                    {'number': 'VY0Lift3', 'type': 'lift', 'name': 'Lift 3'},
                    {'number': 'VY0Lift4', 'type': 'lift', 'name': 'Lift 4'},
                    {'number': 'VY0Lift5', 'type': 'lift', 'name': 'Lift 5'},
                    {'number': 'VY0Lift6', 'type': 'lift', 'name': 'Lift 6'},
                    {'number': 'VY0Lift7', 'type': 'lift', 'name': 'Lift 7'},
                    {'number': 'VY0Lift8', 'type': 'lift', 'name': 'Lift 8'},
                ]
                
                for config in gf_rooms:
                    room = Room(
                        floor_id=floor.id,
                        number=config['number'],
                        name=config['name'],
                        room_type=config['type']
                    )
                    db.session.add(room)
                    print(f"     Created: {config['number']} - {config['name']}")

            elif floor.level == 6:
                # 6TH FLOOR (Meeting & Conference Rooms)
                room_configs = [
                    {'number': 'VY613', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 613'},
                    {'number': 'VY610', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 610'},
                    {'number': 'VY602', 'type': Room.ROOM_TYPE_CONFERENCE, 'name': 'Conference Room 602'},
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
                    {'number': 'VY609', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 609'},
                    {'number': 'VY615', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 615'},
                    {'number': 'VY614', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 614'},
                    {'number': 'VY616', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom 616'},
                ]
                for config in room_configs:
                    room = Room(floor_id=floor.id, number=config['number'], name=config['name'], room_type=config['type'])
                    db.session.add(room)
                    print(f"     Created: {config['number']} - {config['name']}")
                    
            elif floor.level == 7:
                # 7TH FLOOR (Kitchens & Labs)
                room_configs = [
                    {'number': 'VY706', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Main Kitchen 706'},
                    {'number': 'VY715', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Prep Kitchen 715'},
                    {'number': 'VY712', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Pastry Kitchen 712'},
                    {'number': 'VY714', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Kitchen 714'},
                    {'number': 'VY713', 'type': Room.ROOM_TYPE_KITCHEN, 'name': 'Kitchen 713'},
                    {'number': 'VY726', 'type': Room.ROOM_TYPE_LAB, 'name': 'Lab 726'},
                    {'number': 'VY707', 'type': 'faculty', 'name': 'Faculty Room 707'},
                ]
                for config in room_configs:
                    room = Room(floor_id=floor.id, number=config['number'], name=config['name'], room_type=config['type'])
                    db.session.add(room)
                    print(f"     Created: {config['number']} - {config['name']}")
                    
            else:
                # GENERIC LAYOUT
                floor_prefix = f"VY{floor.level}"
                room_configs = [
                    {'suffix': '01', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': f'Classroom {floor.level}01'},
                    {'suffix': '02', 'type': Room.ROOM_TYPE_CLASSROOM, 'name': f'Classroom {floor.level}02'},
                    {'suffix': '05', 'type': Room.ROOM_TYPE_LAB, 'name': f'Lab {floor.level}05'},
                    {'suffix': '10', 'type': Room.ROOM_TYPE_WASHROOM, 'name': 'Washroom'},
                ]
                for config in room_configs:
                    room = Room(floor_id=floor.id, number=f"{floor_prefix}{config['suffix']}", name=config['name'], room_type=config['type'])
                    db.session.add(room)
                    print(f"     Created: {floor_prefix}{config['suffix']}")
            
        db.session.commit()
        
        # Create assets for rooms
        print("\n Creating Assets...")
        all_rooms = Room.query.all()
        
        for room in all_rooms:
            # Add assets based on room type
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
            elif room.room_type == Room.ROOM_TYPE_KITCHEN:
                assets = [
                    {'name': 'Commercial Stove', 'type': 'stove'},
                    {'name': 'Industrial Exhaust System', 'type': 'exhaust'},
                    {'name': 'Walk-in Refrigerator', 'type': 'fridge'},
                    {'name': 'Prep Stations', 'type': 'prep_station'},
                    {'name': 'Industrial Oven', 'type': 'oven'},
                    {'name': 'Fire Extinguisher', 'type': 'safety'},
                ]
            elif room.room_type in [Room.ROOM_TYPE_CONFERENCE, Room.ROOM_TYPE_MEETING]:
                assets = [
                    {'name': 'Conference Table', 'type': 'table'},
                    {'name': 'Presentation Display', 'type': 'display'},
                    {'name': 'Video Conferencing Kit', 'type': 'camera'},
                    {'name': 'AC Unit', 'type': 'ac'},
                ]
            else:
                assets = [
                    {'name': 'Lights', 'type': 'light'},
                    {'name': 'Exhaust Fan', 'type': 'fan'},
                ]
            
            for asset_data in assets:
                asset = Asset(
                    room_id=room.id,
                    name=asset_data['name'],
                    asset_type=asset_data['type'],
                    status=Asset.STATUS_WORKING,
                    # Random installation date between 0 and 5 years ago
                    installation_date=datetime.utcnow() - timedelta(days=random.randint(0, 365 * 5))
                )
                db.session.add(asset)
            
            print(f"   Created {len(assets)} assets for {room.number}")
        
        db.session.commit()
        
        # Summary
        room_count = Room.query.count()
        asset_count = Asset.query.count()
        
        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("=" * 60)
        print(f"\n Summary:")
        print(f"   Building: Vyas")
        print(f"   Floors: {len(floors)}")
        print(f"   Rooms: {room_count}")
        print(f"   Assets: {asset_count}")
        
        print("\n Vyas building data created successfully!")
        print("   You can now start the server with: python run.py")
        print("=" * 60)


if __name__ == '__main__':
    create_vyas_data()
