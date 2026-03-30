#!/bin/bash
# Check production database state for cycles and subject offerings

echo "=== Production Database State Check ==="
echo ""

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    echo "Run this on Railway: railway run bash check_production_cycles.sh"
    exit 1
fi

echo "1. Cycles by semester:"
psql "$DATABASE_URL" -c "
    SELECT c.id, c.semester_id, s.label AS semester_label, c.status, c.academic_year_id
    FROM cycle c
    JOIN semester s ON s.id = c.semester_id
    ORDER BY c.semester_id;
"

echo ""
echo "2. Subject offerings by semester:"
psql "$DATABASE_URL" -c "
    SELECT semester_id, s.label AS semester_label, COUNT(*) AS offering_count
    FROM subject_offering so
    JOIN semester s ON s.id = so.semester_id
    GROUP BY semester_id, s.label
    ORDER BY semester_id;
"

echo ""
echo "3. Open cycles:"
psql "$DATABASE_URL" -c "
    SELECT c.id, s.label AS semester, c.status, 
           (SELECT COUNT(*) FROM subject_offering so WHERE so.semester_id = c.semester_id) AS offerings
    FROM cycle c
    JOIN semester s ON s.id = c.semester_id
    WHERE c.status = 'OPEN'
    ORDER BY c.semester_id;
"

echo ""
echo "=== End of Check ==="
