#!/usr/bin/env python3
"""
Demo Data Seeding Script for FWMS

This script seeds the database with realistic demo data for testing purposes.
It creates:
- An active academic cycle (Even Semester 2025-26)
- 6-8 subject offerings for MCA/BCA programs
- Sample workload allocations for demo viewing

Run: python scripts/seed_demo_data.py

Requirements:
- DATABASE_URL environment variable set
- psycopg2 package installed
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection from environment variable"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

def check_demo_data_exists(cursor):
    """Check if demo data already exists"""
    # Check for Even Semester 2025-26 cycle
    cursor.execute("""
        SELECT c.id 
        FROM cycle c
        JOIN academic_year ay ON c.academic_year_id = ay.id
        WHERE ay.name = '2025-2026'
        LIMIT 1
    """)
    
    if cursor.fetchone():
        return True
    return False

def seed_academic_year(cursor):
    """Create academic year 2025-2026 if it doesn't exist"""
    cursor.execute("""
        INSERT INTO academic_year (name, start_date, end_date)
        VALUES ('2025-2026', '2025-07-01', '2026-06-30')
        ON CONFLICT (name) DO NOTHING
        RETURNING id
    """)
    
    result = cursor.fetchone()
    if result:
        print("✅ Created academic year: 2025-2026")
        return result[0]
    else:
        # Already exists, fetch it
        cursor.execute("SELECT id FROM academic_year WHERE name = '2025-2026'")
        return cursor.fetchone()[0]

def seed_cycles(cursor, academic_year_id):
    """Create cycles for even semesters (II, IV, VI)"""
    # Get even semester IDs
    cursor.execute("SELECT id, label FROM semester WHERE label IN ('II', 'IV', 'VI')")
    semesters = cursor.fetchall()
    
    cycle_ids = []
    for sem_id, sem_label in semesters:
        cursor.execute("""
            INSERT INTO cycle (academic_year_id, semester_id, status, is_open, opened_at)
            VALUES (%s, %s, 'OPEN', true, NOW())
            ON CONFLICT (academic_year_id, semester_id) DO UPDATE
            SET status = 'OPEN', is_open = true, opened_at = NOW()
            RETURNING id
        """, (academic_year_id, sem_id))
        
        cycle_id = cursor.fetchone()[0]
        cycle_ids.append((cycle_id, sem_label))
        print(f"✅ Created/updated cycle for Semester {sem_label} (ID: {cycle_id})")
    
    return cycle_ids

def seed_subject_offerings(cursor, academic_year_id):
    """Create realistic subject offerings for MCA/BCA programs"""
    
    # Get program IDs
    cursor.execute("SELECT id, name FROM program WHERE name IN ('MCA', 'BCA')")
    programs = dict(cursor.fetchall())
    
    if not programs:
        print("⚠️  WARNING: No MCA/BCA programs found. Creating them...")
        cursor.execute("""
            INSERT INTO program (name, ug_pg, is_active)
            VALUES ('MCA', 'PG', true), ('BCA', 'UG', true)
            ON CONFLICT (name) DO NOTHING
        """)
        cursor.execute("SELECT id, name FROM program WHERE name IN ('MCA', 'BCA')")
        programs = dict(cursor.fetchall())
    
    # Get semester IDs
    cursor.execute("SELECT id, label FROM semester WHERE label IN ('II', 'III', 'IV')")
    semesters = dict(cursor.fetchall())
    
    # Get section A, Shift 1
    cursor.execute("SELECT id FROM section WHERE label = 'A' AND shift = 1 LIMIT 1")
    section_result = cursor.fetchone()
    if not section_result:
        cursor.execute("""
            INSERT INTO section (label, student_strength, shift)
            VALUES ('A', 60, 1)
            RETURNING id
        """)
        section_result = cursor.fetchone()
    section_id = section_result[0]
    
    # Define realistic subjects
    subjects_to_create = [
        # MCA Semester II (Even)
        {
            'code': 'CCA201', 'name': 'Machine Learning', 
            'program': 'MCA', 'semester': 'II', 'l': 3, 't': 0, 'p': 2, 'tch': 5
        },
        {
            'code': 'CCA202', 'name': 'Full Stack Web Development',
            'program': 'MCA', 'semester': 'II', 'l': 3, 't': 0, 'p': 2, 'tch': 5
        },
        {
            'code': 'CCA203', 'name': 'Advanced Database Technologies',
            'program': 'MCA', 'semester': 'II', 'l': 3, 't': 0, 'p': 2, 'tch': 5
        },
        # BCA Semester II (Even)
        {
            'code': 'ACA201', 'name': 'Object Oriented Programming',
            'program': 'BCA', 'semester': 'II', 'l': 3, 't': 1, 'p': 0, 'tch': 4
        },
        {
            'code': 'ACA202', 'name': 'Data Structures',
            'program': 'BCA', 'semester': 'II', 'l': 3, 't': 0, 'p': 2, 'tch': 5
        },
        # BCA Semester IV (Even)
        {
            'code': 'ACA401', 'name': 'Software Engineering',
            'program': 'BCA', 'semester': 'IV', 'l': 3, 't': 0, 'p': 2, 'tch': 5
        },
        {
            'code': 'ACA402', 'name': 'Web Technologies',
            'program': 'BCA', 'semester': 'IV', 'l': 2, 't': 0, 'p': 4, 'tch': 6
        },
    ]
    
    offering_ids = []
    for subj in subjects_to_create:
        # Create subject if it doesn't exist
        cursor.execute("""
            INSERT INTO subject (code, name, l, t, p, tch, credits, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (code) DO UPDATE
            SET name = EXCLUDED.name, l = EXCLUDED.l, t = EXCLUDED.t, 
                p = EXCLUDED.p, tch = EXCLUDED.tch
            RETURNING id
        """, (subj['code'], subj['name'], subj['l'], subj['t'], subj['p'], 
              subj['tch'], subj['l'] + subj['t'] + subj['p']))
        
        subject_id = cursor.fetchone()[0]
        
        # Create subject offering
        program_id = programs.get(subj['program'])
        semester_id = semesters.get(subj['semester'])
        
        if program_id and semester_id:
            cursor.execute("""
                INSERT INTO subject_offering (
                    subject_id, program_id, semester_id, section_id,
                    shift, student_strength, academic_year, academic_year_id, is_active
                )
                VALUES (%s, %s, %s, %s, 1, 60, '2025-2026', %s, true)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (subject_id, program_id, semester_id, section_id, academic_year_id))
            
            result = cursor.fetchone()
            if result:
                offering_id = result[0]
                offering_ids.append(offering_id)
                print(f"✅ Created subject offering: {subj['code']} - {subj['name']}")
    
    return offering_ids

def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("🌱 FWMS Demo Data Seeding Script")
    print("="*60 + "\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if demo data already exists
        if check_demo_data_exists(cursor):
            print("ℹ️  Demo data already seeded, skipping")
            print("   (Delete cycles for 2025-2026 to re-seed)")
            return
        
        # Start transaction
        print("\n📦 Starting demo data seeding...\n")
        
        # Step 1: Create academic year
        academic_year_id = seed_academic_year(cursor)
        
        # Step 2: Create cycles for even semesters
        cycle_ids = seed_cycles(cursor, academic_year_id)
        
        # Step 3: Create subject offerings
        offering_ids = seed_subject_offerings(cursor, academic_year_id)
        
        # Commit transaction
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ Demo data seeding completed successfully!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   - Academic Year: 2025-2026")
        print(f"   - Cycles created: {len(cycle_ids)}")
        print(f"   - Subject offerings: {len(offering_ids)}")
        print(f"\n💡 Demo users can now log in and see workload data!")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
