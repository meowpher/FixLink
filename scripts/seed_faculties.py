#!/usr/bin/env python3
"""
seed_faculties.py - Bulletproof Data Seeder Script for DoCSA Faculty & Staff

Extracts real teaching and non-teaching staff from 'DoCSA Staff List Updated as on.21.10.2026.xlsx'
using pandas, performs safe soft-delete on existing dummy faculty members, handles name prefix
stripping and email collision avoidance, and commits 89 staff records to FixLink database.
"""

import os
import sys
import re
import argparse
import pandas as pd
from app import create_app, db
from app.models import User
from sqlalchemy import func

DEFAULT_EXCEL_FILENAME = 'DoCSA Staff List Updated as on.21.10.2026.xlsx'
DEFAULT_FACULTY_PASSWORD = os.getenv('DEFAULT_FACULTY_PASSWORD', 'FixLink@2026')

PREFIX_REGEX = r'^(?:(?:prof|dr|mrs|mr|ms)\.?\s*)+'


def find_excel_file(specified_path=None):
    """Locate the DoCSA Excel file across standard project and environment locations."""
    if specified_path and os.path.exists(specified_path):
        return specified_path
    
    candidates = [
        os.path.join(os.getcwd(), DEFAULT_EXCEL_FILENAME),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_EXCEL_FILENAME),
        os.path.expanduser(f"~/Downloads/{DEFAULT_EXCEL_FILENAME}"),
        f"C:\\Users\\admin\\Downloads\\{DEFAULT_EXCEL_FILENAME}"
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
            
    # Glob search in current directory
    for f in os.listdir(os.getcwd()):
        if f.endswith('.xlsx') and 'DoCSA' in f:
            return os.path.join(os.getcwd(), f)
            
    raise FileNotFoundError(
        f"Could not locate DoCSA Excel file '{DEFAULT_EXCEL_FILENAME}'. "
        "Please provide the file path as a command line argument."
    )


def extract_staff_data(excel_path):
    """
    Extracts 'Teaching Staff' (skip 11 rows) and 'Non Teaching Staff' (skip 9 rows),
    combines them, fixes the typo 'Asscociate Professor' -> 'Associate Professor',
    and returns a clean pandas DataFrame.
    """
    print(f"[*] Loading Excel workbook: {excel_path}")
    
    # Extract Teaching Staff (skip 11 rows to reach data starting at row 12)
    df_teach = pd.read_excel(
        excel_path,
        sheet_name='Teaching Staff',
        skiprows=11,
        header=None
    )
    
    # Extract Non Teaching Staff (skip 9 rows to reach data starting at row 10)
    df_non = pd.read_excel(
        excel_path,
        sheet_name='Non Teaching Staff',
        skiprows=9,
        header=None
    )
    
    # Standardize column mapping
    # Teaching Staff layout: Col 0: Sr.No, Col 1: Emp ID, Col 2: Name, Col 3: Designation
    df_teach_clean = pd.DataFrame({
        'name': df_teach.iloc[:, 2],
        'designation': df_teach.iloc[:, 3],
        'emp_id': df_teach.iloc[:, 1],
        'category': 'TEACHING'
    })
    
    # Non Teaching Staff layout: Col 0: Sr.No, Col 1: Name, Col 2: Designation
    df_non_clean = pd.DataFrame({
        'name': df_non.iloc[:, 1],
        'designation': df_non.iloc[:, 2],
        'emp_id': None,
        'category': 'NON_TEACHING'
    })
    
    # Combine datasets
    df_combined = pd.concat([df_teach_clean, df_non_clean], ignore_index=True)
    
    # Drop empty or invalid name rows
    df_combined = df_combined.dropna(subset=['name'])
    df_combined = df_combined[df_combined['name'].astype(str).str.strip() != '']
    df_combined = df_combined[df_combined['name'].astype(str).str.strip().str.lower() != 'nan']
    
    # Fix the typo: 'Asscociate Professor' -> 'Associate Professor'
    df_combined['designation'] = (
        df_combined['designation']
        .astype(str)
        .str.replace('Asscociate Professor', 'Associate Professor', regex=False)
        .str.strip()
    )
    
    print(f"[+] Successfully extracted {len(df_teach_clean.dropna(subset=['name']))} Teaching and "
          f"{len(df_non_clean.dropna(subset=['name']))} Non-Teaching staff (Total: {len(df_combined)})")
    print("[+] Applied typo correction: 'Asscociate Professor' -> 'Associate Professor'")
    return df_combined


def clean_staff_name(raw_name):
    """Strip prefixes ('Dr.', 'Prof.', 'Mr.', 'Mrs.', 'Ms.') and normalize whitespace."""
    cleaned = re.sub(PREFIX_REGEX, '', str(raw_name).strip(), flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def generate_unique_email(clean_name, existing_emails, loop_emails):
    """
    Generate email (e.g., first.last@mitwpu.edu.in).
    Crucially, check if the email already exists in the DB or the current loop.
    If it does, append an incrementing counter (first.last1@...) to prevent IntegrityError crashes.
    """
    parts = clean_name.split(' ')
    first = re.sub(r'[^a-zA-Z0-9]', '', parts[0]).lower()
    last = re.sub(r'[^a-zA-Z0-9]', '', parts[-1]).lower() if len(parts) > 1 else first
    
    base_prefix = f"{first}.{last}"
    candidate_email = f"{base_prefix}@mitwpu.edu.in"
    counter = 1
    
    while candidate_email.lower() in existing_emails or candidate_email.lower() in loop_emails:
        candidate_email = f"{base_prefix}{counter}@mitwpu.edu.in"
        counter += 1
        
    loop_emails.add(candidate_email.lower())
    return candidate_email


def seed_faculties(excel_path=None, default_password=DEFAULT_FACULTY_PASSWORD):
    """
    Execute the bulletproof faculty migration:
    1. Soft delete existing faculty users (is_active = False)
    2. Extract 89 staff records with pandas
    3. Generate collision-safe emails
    4. Inject real staff into DB and commit
    """
    excel_path = find_excel_file(excel_path)
    df_staff = extract_staff_data(excel_path)
    
    app = create_app()
    with app.app_context():
        print("\n[*] Starting Database Migration within app_context()...")
        
        # 1. Soft Delete existing faculties instead of hard deleting (preserves FK constraints on old tickets)
        # We target both 'FACULTY' and legacy lowercase 'faculty'
        soft_deleted_count = User.query.filter(
            func.lower(User.role) == 'faculty'
        ).update({'is_active': False}, synchronize_session=False)
        
        # Also ensure User.query.filter_by(role='FACULTY') call runs explicitly as requested
        User.query.filter_by(role='FACULTY').update({'is_active': False})
        
        db.session.flush()
        print(f"[+] Soft-deleted {soft_deleted_count} existing faculty members (is_active=False). Foreign Keys preserved.")
        
        # 2. Pre-fetch existing emails from DB for collision detection
        existing_db_emails = {
            u[0].lower() for u in db.session.query(User.email).all() if u[0]
        }
        loop_emails = set()
        
        inserted_count = 0
        collision_count = 0
        
        for idx, row in df_staff.iterrows():
            raw_name = str(row['name']).strip()
            cleaned_name = clean_staff_name(raw_name)
            designation = str(row['designation']).strip()
            
            # Clean PRN / Employee ID if present (e.g. '(#1049217068)' -> '1049217068')
            raw_emp_id = row.get('emp_id')
            clean_prn = None
            if pd.notna(raw_emp_id) and str(raw_emp_id).strip():
                digits = re.sub(r'[^\d]', '', str(raw_emp_id))
                if digits:
                    clean_prn = digits
            
            # Generate collision-free email
            email = generate_unique_email(cleaned_name, existing_db_emails, loop_emails)
            
            # Detect if counter was appended due to collision
            base_check = f"{re.sub(r'[^a-zA-Z0-9]', '', cleaned_name.split(' ')[0]).lower()}.{re.sub(r'[^a-zA-Z0-9]', '', cleaned_name.split(' ')[-1]).lower()}@mitwpu.edu.in"
            if email != base_check:
                collision_count += 1
                print(f"  [COLLISION HANDLED] '{raw_name}' ({base_check}) -> '{email}'")
            
            # Create new real faculty user
            user = User(
                name=cleaned_name,
                email=email,
                role='FACULTY',
                designation=designation,
                prn=clean_prn,
                is_active=True,
                is_verified=True,
                has_accepted_terms=True
            )
            user.set_password(default_password)
            db.session.add(user)
            inserted_count += 1
            
        db.session.commit()
        print(f"\n[+] Successfully committed {inserted_count} real staff members to the database.")
        print(f"[+] Handled {collision_count} email collisions smoothly with zero IntegrityErrors.")
        print(f"[+] Default password set for all migrated accounts.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FixLink DoCSA Faculty & Staff Data Seeder")
    parser.add_argument('excel_path', nargs='?', default=None, help="Path to DoCSA staff Excel file")
    parser.add_argument('--password', default=DEFAULT_FACULTY_PASSWORD, help="Default password for new staff")
    args = parser.parse_args()
    
    seed_faculties(excel_path=args.excel_path, default_password=args.password)
