db_url = [l.split('=',1)[1].strip() for l in open('.env').readlines() if l.startswith('DATABASE_URL')][0]
from sqlalchemy import create_engine, text
engine = create_engine(db_url)
with engine.connect() as conn:
    print("=== PROGRAMS (MCA) ===")
    rows = conn.execute(text("SELECT id, name FROM program WHERE name ILIKE '%MCA%'")).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== SEMESTERS ===")
    rows = conn.execute(text("SELECT id, name, label FROM semester ORDER BY id")).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== SECTIONS ===")
    rows = conn.execute(text("SELECT id, name, label FROM section ORDER BY id")).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== ACADEMIC YEAR ===")
    rows = conn.execute(text("SELECT id, year FROM academic_year ORDER BY id DESC LIMIT 3")).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== EXISTING MCA SUBJECTS IN subject TABLE ===")
    rows = conn.execute(text("""
        SELECT id, code, name, l, t, p, tch, credits, course_category, curriculum_year
        FROM subject WHERE code ILIKE 'CCA%' OR code ILIKE 'CMA%' OR code ILIKE 'CCM%' OR code ILIKE 'CEL%'
        ORDER BY code
    """)).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== EXISTING MCA OFFERINGS ===")
    rows = conn.execute(text("""
        SELECT so.id, so.program_id, so.semester_id, so.section_id, so.shift, sub.code, sub.name
        FROM subject_offering so
        JOIN subject sub ON sub.id = so.subject_id
        JOIN program p ON p.id = so.program_id
        WHERE p.name ILIKE '%MCA%'
        ORDER BY so.semester_id, sub.code
    """)).fetchall()
    for r in rows: print(dict(r._mapping))
    
    print("\n=== DUPLICATE PROGRAMS ===")
    rows = conn.execute(text("""
        SELECT UPPER(REPLACE(name,' ','')) as key, array_agg(id ORDER BY id) as ids,
               array_agg(name ORDER BY id) as names
        FROM program
        GROUP BY UPPER(REPLACE(name,' ',''))
        HAVING COUNT(*) > 1
    """)).fetchall()
    for r in rows: print(dict(r._mapping))
