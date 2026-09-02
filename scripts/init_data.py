#!/usr/bin/env python3
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false
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

def create_vyas_data(app=None, interactive=False):
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
            print("\n  Vyas building already exists.")
            if not interactive:
                print("  Non-interactive mode: skipping recreation.")
                return
            try:
                response = input("Do you want to reset and recreate all data? (y/N): ")
            except (EOFError, OSError):
                print("  No input stream available: skipping recreation.")
                return
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
        
        # Create rooms for each floor using FLOOR_DEFINITIONS
        print("\n Creating Rooms...")
        from scripts.sync_rooms import FLOOR_DEFINITIONS
        
        for floor in floors:
            print(f"\n   Creating rooms for {floor.name}...")
            definitions = FLOOR_DEFINITIONS.get(floor.level, [])
            for config in definitions:
                room = Room(
                    floor_id=floor.id,
                    number=config['number'],
                    name=config['name'],
                    room_type=config['type']
                )
                db.session.add(room)
                print(f"     Created: {config['number']} - {config['name']}")
            
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
