/*
 * Migration 038: Set curriculum_year for all subjects with NULL values
 * 
 * Purpose: Ensure all subjects have a curriculum_year value for display in UI
 * 
 * Logic:
 * - MCA subjects (CCA, CCM, CMA, CEL prefixes) → 2022 regulation
 * - BCA subjects (ACA, ACY, ACM, GMA, GLS, GGE, ABB, ASS prefixes) → 2023 regulation
 * - Any remaining NULL subjects → 2022 as default
 */

BEGIN;

-- Ensure column exists (idempotent)
ALTER TABLE subject ADD COLUMN IF NOT EXISTS curriculum_year VARCHAR(20) DEFAULT '2022';

-- Set MCA subjects (codes starting with CCA, CCM, CMA, CEL) to 2022
UPDATE subject SET curriculum_year = '2022'
WHERE (code LIKE 'CCA%' OR code LIKE 'CCM%' OR code LIKE 'CMA%' OR code LIKE 'CEL%')
  AND (curriculum_year IS NULL OR curriculum_year = '');

-- Set BCA subjects (codes starting with ACA, ACY, ACM, GMA, GLS, GGE, ABB, ASS) to 2023
UPDATE subject SET curriculum_year = '2023'
WHERE (code LIKE 'ACA%' OR code LIKE 'ACY%' OR code LIKE 'ACM%'
       OR code LIKE 'GMA%' OR code LIKE 'GLS%' OR code LIKE 'GGE%'
       OR code LIKE 'ABB%' OR code LIKE 'ASS%')
  AND (curriculum_year IS NULL OR curriculum_year = '');

-- Set any remaining NULL subjects to 2022 as default
UPDATE subject SET curriculum_year = '2022'
WHERE curriculum_year IS NULL OR curriculum_year = '';

-- Verify counts by curriculum year
SELECT curriculum_year, COUNT(*) as count 
FROM subject 
GROUP BY curriculum_year 
ORDER BY curriculum_year;

COMMIT;
