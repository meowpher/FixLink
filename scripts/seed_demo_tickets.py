#!/usr/bin/env python3
"""
Seed realistic demo tickets and certified professionals for FixLink.
Provides rich real data for Insights / Analytics metrics and charts.
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Room, Ticket, Professional

def seed_demo_data():
    app = create_app()
    with app.app_context():
        print("Checking professionals and maintenance tickets...")
        
        # 1. Ensure Professionals exist
        profs_data = [
            {"name": "Ramesh Sharma", "email": "ramesh.sharma@mitwpu.edu.in", "phone": "+91 98234 11223", "category": "electrical"},
            {"name": "Sunil Patil", "email": "sunil.patil@mitwpu.edu.in", "phone": "+91 98234 44556", "category": "it_technician"},
            {"name": "Vikas Jadhav", "email": "vikas.jadhav@mitwpu.edu.in", "phone": "+91 98234 77889", "category": "plumber"},
            {"name": "Mahesh Shinde", "email": "mahesh.shinde@mitwpu.edu.in", "phone": "+91 98234 99001", "category": "carpenter"},
        ]
        
        created_profs = []
        for pdata in profs_data:
            existing = Professional.query.filter_by(email=pdata["email"]).first()
            if not existing:
                prof = Professional(
                    username=pdata["email"].split("@")[0],
                    name=pdata["name"],
                    email=pdata["email"],
                    phone=pdata["phone"],
                    category=pdata["category"],
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=60)
                )
                prof.set_password("Professional@123")
                db.session.add(prof)
                created_profs.append(prof)
            else:
                created_profs.append(existing)
                
        db.session.commit()
        
        # 2. Get Rooms
        rooms = Room.query.limit(30).all()
        if not rooms:
            print("No rooms found in database.")
            return

        # 3. Create Sample Tickets if none exist
        if Ticket.query.count() > 0:
            print(f"Tickets already exist ({Ticket.query.count()} tickets). Skipping ticket seed.")
            return
            
        now = datetime.utcnow()
        ticket_templates = [
            ("projector", "Projector display flickering intermittently during morning lectures.", "it_technician", "fixed", 1.8),
            ("ac", "AC cooling is insufficient, temperature sensor error code E4.", "electrical", "fixed", 2.4),
            ("lighting", "Tube lights not turning on near back rows.", "electrical", "fixed", 1.2),
            ("computer", "Lab PC 18 not booting up, power button flashing amber.", "it_technician", "fixed", 2.0),
            ("plumbing", "Water faucet leaking continuously in washroom.", "plumber", "fixed", 1.1),
            ("furniture", "Whiteboard marker tray broken off wall bracket.", "carpenter", "fixed", 2.8),
            ("electrical", "Main switchboard sparking when turning on room power.", "electrical", "fixed", 3.1),
            ("chairs", "Three rolling chairs have broken wheel casters.", "carpenter", "fixed", 1.5),
            ("projector", "HDMI connection from instructor desk no audio.", "it_technician", "fixed", 1.4),
            ("ac", "AC compressor making loud rattling noise.", "electrical", "fixed", 3.5),
            ("lighting", "Emergency exit light battery backup dead.", "electrical", "fixed", 2.0),
            ("plumbing", "Drain pipe clogged in science lab sink.", "plumber", "fixed", 1.6),
            ("door_error", "Door lock latch stuck, cannot lock room securely.", "carpenter", "fixed", 1.9),
            ("computer", "Ethernet port at desk row 2 has loose connection.", "it_technician", "fixed", 2.2),
            ("electrical", "Power outlet near podium not supplying current.", "electrical", "in-progress", None),
            ("lighting", "Front row ceiling LED panel dimmed and buzzing.", "electrical", "in-progress", None),
            ("projector", "Ceiling projector mount loose and shaking.", "it_technician", "in-progress", None),
            ("furniture", "Instructor podium corner laminate peeling off.", "carpenter", "in-progress", None),
            ("plumbing", "Water cooler filter replacement alert triggered.", "plumber", "in-progress", None),
            ("ac", "Air conditioner remote sensor not responding.", "electrical", "assigned", None),
            ("computer", "Audio microphone feedback issue in conference room.", "it_technician", "assigned", None),
            ("lighting", "Stairwell light broken between 3rd and 4th floor.", "electrical", "assigned", None),
            ("door_error", "Door handle loose on classroom entrance.", "carpenter", "open", None),
            ("electrical", "Extension power cord damaged near AV cabinet.", "electrical", "open", None),
        ]
        
        prof_by_category = {p.category: p for p in created_profs}
        
        for issue_type, desc, cat, status, fix_hours in ticket_templates:
            day_offset = random.randint(1, 26)
            created_at = now - timedelta(days=day_offset, hours=random.randint(1, 10))
            assigned_prof = prof_by_category.get(cat)
            room = random.choice(rooms)
            fixed_at = (created_at + timedelta(hours=fix_hours)) if (status == "fixed" and fix_hours) else None
            
            ticket = Ticket(
                room_id=room.id,
                issue_type=issue_type,
                description=desc,
                status=status,
                created_at=created_at,
                updated_at=fixed_at or created_at,
                fixed_at=fixed_at,
                job_completed_at=fixed_at,
                assigned_professional_id=assigned_prof.id if assigned_prof and status != "open" else None,
                reporter_name="Kiran Verma",
                reporter_email="kiran@mitwpu.edu.in",
                prn="1032210884",
                complexity="Medium" if status == "fixed" else None
            )
            db.session.add(ticket)
            
        db.session.commit()
        print(f"Seeded {len(ticket_templates)} demo maintenance tickets.")

if __name__ == '__main__':
    seed_demo_data()
