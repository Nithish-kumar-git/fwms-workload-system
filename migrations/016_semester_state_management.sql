-- ============================================================================
-- PHASE 2: Semester State Management
-- Add state tracking for semester workflow control
-- ============================================================================

-- Add state column to track semester workflow
-- States: OPEN, CLOSED, ALLOCATED, FROZEN
ALTER TABLE semester
ADD COLUMN IF NOT EXISTS state VARCHAR(20) DEFAULT 'CLOSED';

-- Add constraint to ensure valid states
ALTER TABLE semester
ADD CONSTRAINT chk_semester_state 
CHECK (state IN ('OPEN', 'CLOSED', 'ALLOCATED', 'FROZEN'));

-- Add index for state queries
CREATE INDEX IF NOT EXISTS idx_semester_state ON semester(state);

-- Add metadata columns for state transitions
ALTER TABLE semester
ADD COLUMN IF NOT EXISTS opened_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS allocated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS frozen_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS frozen_by_staff_id BIGINT;

-- Add foreign key for frozen_by
ALTER TABLE semester
ADD CONSTRAINT fk_semester_frozen_by 
FOREIGN KEY (frozen_by_staff_id) REFERENCES staff(id);

-- Add index for frozen_by queries
CREATE INDEX IF NOT EXISTS idx_semester_frozen_by ON semester(frozen_by_staff_id);

COMMENT ON COLUMN semester.state IS 'Workflow state: OPEN (preferences), CLOSED (ready for allocation), ALLOCATED (allocation done), FROZEN (finalized by HOD)';
COMMENT ON COLUMN semester.opened_at IS 'Timestamp when semester was opened for preferences';
COMMENT ON COLUMN semester.closed_at IS 'Timestamp when semester was closed (preferences locked)';
COMMENT ON COLUMN semester.allocated_at IS 'Timestamp when allocation was completed';
COMMENT ON COLUMN semester.frozen_at IS 'Timestamp when semester was frozen by HOD';
COMMENT ON COLUMN semester.frozen_by_staff_id IS 'Staff ID of HOD who froze the semester';
