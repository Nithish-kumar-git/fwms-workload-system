-- ============================================================================
-- Migration 036: Add Curriculum Year to Subjects and Class Teacher Assignment
-- Purpose: Track regulation/curriculum year for subjects and CT assignments
-- ============================================================================

BEGIN;

-- Add curriculum_year to subject table
ALTER TABLE subject ADD COLUMN IF NOT EXISTS curriculum_year VARCHAR(20) DEFAULT '2022';

-- MCA subjects (CCA, CCM, CMA, CEL prefixes) = 2022 regulation
UPDATE subject SET curriculum_year = '2022'
WHERE code LIKE 'CCA%' OR code LIKE 'CCM%' OR code LIKE 'CMA%' OR code LIKE 'CEL%';

-- BCA subjects (ACA, ACY, ACM, GMA, GLS, GGE, ABB, ASS prefixes) = 2023 regulation
UPDATE subject SET curriculum_year = '2023'
WHERE code LIKE 'ACA%' OR code LIKE 'ACY%' OR code LIKE 'ACM%'
   OR code LIKE 'GMA%' OR code LIKE 'GLS%' OR code LIKE 'GGE%'
   OR code LIKE 'ABB%' OR code LIKE 'ASS%';

-- Add curriculum year to CT assignment in staff table
ALTER TABLE staff ADD COLUMN IF NOT EXISTS ct_curriculum_year VARCHAR(20) DEFAULT NULL;

COMMIT;
