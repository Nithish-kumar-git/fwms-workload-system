-- Open ALL even semester cycles for current academic year
UPDATE cycle SET status = 'OPEN', opened_at = NOW()
WHERE semester_id IN (2, 4, 6)
  AND academic_year_id = (SELECT id FROM academic_year WHERE name = '2025-2026');

-- Close odd semester cycles (no subjects exist for them)
UPDATE cycle SET status = 'CLOSED'
WHERE semester_id IN (1, 3, 5);

-- Verify
DO $$
DECLARE
    open_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO open_count FROM cycle WHERE status = 'OPEN';
    RAISE NOTICE '025: open cycles=%', open_count;
END $$;
