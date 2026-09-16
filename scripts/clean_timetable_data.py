"""
Retroactive Database Data Clean-up Script
Normalizes raw timetable strings into structured Subject, Course, and Division fields.
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Timetable
from app.blueprints.faculty.routes import parse_timetable_subject_metadata

def clean_timetables(dry_run=False):
    app = create_app()
    with app.app_context():
        timetables = Timetable.query.all()
        print(f"Total timetable records found: {len(timetables)}")
        
        updated_count = 0
        
        for tt in timetables:
            raw_subj = tt.subject or ''
            raw_course = tt.course or ''
            raw_division = tt.division or ''
            
            # Combine raw info to parse full context if needed
            parse_target = raw_subj
            if raw_course and raw_course not in parse_target:
                parse_target = f"{raw_course} {parse_target}"
            if raw_division and raw_division not in parse_target:
                parse_target = f"{parse_target} {raw_division}"
                
            meta = parse_timetable_subject_metadata(parse_target)
            
            new_subject = meta['subject']
            new_course = meta['course'] or tt.course
            new_division = meta['division'] or tt.division
            
            # Check if changes are needed
            if (new_subject != tt.subject) or (new_course != tt.course) or (new_division != tt.division):
                print(f"[ID #{tt.id}]")
                print(f"  BEFORE -> Subject: '{tt.subject}', Course: '{tt.course}', Div: '{tt.division}'")
                print(f"  AFTER  -> Subject: '{new_subject}', Course: '{new_course}', Div: '{new_division}'")
                print("-" * 60)
                
                if not dry_run:
                    tt.subject = new_subject
                    tt.course = new_course
                    tt.division = new_division
                
                updated_count += 1
                
        if not dry_run and updated_count > 0:
            db.session.commit()
            print(f"\n[SUCCESS] Successfully cleaned and normalized {updated_count} timetable records in the database.")
        elif dry_run:
            print(f"\n[DRY RUN] Would update {updated_count} timetable records. No changes were committed.")
        else:
            print("\n[OK] All timetable records are already normalized.")

if __name__ == '__main__':
    dry_run_flag = '--dry-run' in sys.argv
    clean_timetables(dry_run=dry_run_flag)
