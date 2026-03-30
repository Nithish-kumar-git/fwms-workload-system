#!/bin/bash
# Apply migration 031 to Railway production database

echo "=== Applying Migration 031: Fix Odd Semester Offerings ==="
echo ""
echo "This will:"
echo "  1. Create cycles for semesters I, III, V (if not exist)"
echo "  2. Add subject offerings for odd semesters with CORRECT codes"
echo "  3. Verify counts"
echo ""

# Check if DATABASE_URL is set (Railway auto-sets this)
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    echo "Run this on Railway: railway run bash apply_migration_031.sh"
    exit 1
fi

# Apply migration
psql "$DATABASE_URL" -f migrations/031_fix_odd_semester_offerings.sql

echo ""
echo "=== Migration 031 Applied ==="
echo ""
echo "Verify by checking cycle and subject_offering counts:"
echo "  railway run psql -c 'SELECT semester_id, COUNT(*) FROM subject_offering GROUP BY semester_id ORDER BY semester_id;'"
