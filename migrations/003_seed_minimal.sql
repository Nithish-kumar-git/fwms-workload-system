-- ============================================================================
-- Minimal Seed Data for Integration Verification
-- Purpose: Provides minimal FK-compliant data for testing only
-- ============================================================================

-- Insert 1 staff (required by FK constraints)
INSERT INTO staff (id, email, name, is_coordinator, is_active) VALUES
(1, 'test.staff@example.com', 'Test Staff', false, true);

-- Reset sequence to ensure next auto-generated ID is 2
SELECT setval('staff_id_seq', 1, true);

-- Insert 1 batch
INSERT INTO batch (id, name, is_active) VALUES
(1, 'Test Batch', true);

-- Reset sequence
SELECT setval('batch_id_seq', 1, true);

-- Insert 1 specialization linked to batch
INSERT INTO specialization (id, name, is_active) VALUES
(1, 'Test Specialization', true);

-- Reset sequence
SELECT setval('specialization_id_seq', 1, true);

-- ============================================================================
-- END OF MINIMAL SEED
-- ============================================================================
