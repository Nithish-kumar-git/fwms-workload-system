-- ============================================================================
-- Faculty Subject Selection System — PostgreSQL Schema
-- Conforms to: FSB v1.3
-- Target: PostgreSQL 15+
-- ============================================================================

-- ============================================================================
-- TABLE: staff
-- ============================================================================

CREATE TABLE IF NOT EXISTS staff (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    is_coordinator BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_staff_email_format CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$')
);

CREATE INDEX IF NOT EXISTS idx_staff_email ON staff(email);
CREATE INDEX IF NOT EXISTS idx_staff_is_coordinator ON staff(is_coordinator);

-- ============================================================================
-- TABLE: selection_window
-- ============================================================================

CREATE TABLE IF NOT EXISTS selection_window (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    max_subjects_per_staff INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_window_time_order CHECK (end_time > start_time),
    CONSTRAINT chk_window_max_subjects_positive CHECK (max_subjects_per_staff > 0)
);

CREATE INDEX IF NOT EXISTS idx_selection_window_active ON selection_window(is_active);
CREATE INDEX IF NOT EXISTS idx_selection_window_time_range ON selection_window(start_time, end_time);

-- ============================================================================
-- TABLE: batch
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: specialization
-- ============================================================================

CREATE TABLE IF NOT EXISTS specialization (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: staff_assignment
-- ============================================================================

CREATE TABLE IF NOT EXISTS staff_assignment (
    id BIGSERIAL PRIMARY KEY,
    staff_id BIGINT NOT NULL,
    batch_id BIGINT NOT NULL,
    specialization_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_staff_assignment_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
    CONSTRAINT fk_staff_assignment_batch FOREIGN KEY (batch_id) REFERENCES batch(id) ON DELETE CASCADE,
    CONSTRAINT fk_staff_assignment_specialization FOREIGN KEY (specialization_id) REFERENCES specialization(id) ON DELETE CASCADE,
    CONSTRAINT uq_staff_assignment UNIQUE (staff_id, batch_id, specialization_id)
);

CREATE INDEX IF NOT EXISTS idx_staff_assignment_staff ON staff_assignment(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_assignment_batch_spec ON staff_assignment(batch_id, specialization_id);

-- ============================================================================
-- TABLE: subject
-- ============================================================================

CREATE TABLE IF NOT EXISTS subject (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    batch_id BIGINT NOT NULL,
    specialization_id BIGINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_subject_batch FOREIGN KEY (batch_id) REFERENCES batch(id) ON DELETE CASCADE,
    CONSTRAINT fk_subject_specialization FOREIGN KEY (specialization_id) REFERENCES specialization(id) ON DELETE CASCADE,
    CONSTRAINT uq_subject_batch_spec UNIQUE (id, batch_id, specialization_id)
);

CREATE INDEX IF NOT EXISTS idx_subject_code ON subject(code);
CREATE INDEX IF NOT EXISTS idx_subject_batch_spec ON subject(batch_id, specialization_id);
CREATE INDEX IF NOT EXISTS idx_subject_is_active ON subject(is_active);

-- ============================================================================
-- TABLE: subject_selection
-- ============================================================================

CREATE TABLE IF NOT EXISTS subject_selection (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL,
    staff_id BIGINT NOT NULL,
    batch_id BIGINT NOT NULL,
    specialization_id BIGINT NOT NULL,
    window_id BIGINT NOT NULL,
    staff_slot_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    selected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_subject_selection_subject FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_window FOREIGN KEY (window_id) REFERENCES selection_window(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_batch FOREIGN KEY (batch_id) REFERENCES batch(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_specialization FOREIGN KEY (specialization_id) REFERENCES specialization(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_subject_composite FOREIGN KEY (subject_id, batch_id, specialization_id) REFERENCES subject(id, batch_id, specialization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_selection_eligibility FOREIGN KEY (staff_id, batch_id, specialization_id) REFERENCES staff_assignment(staff_id, batch_id, specialization_id) ON DELETE RESTRICT,
    CONSTRAINT chk_subject_selection_status CHECK (status IN ('SELECTED', 'OVERRIDDEN')),
    CONSTRAINT chk_subject_selection_slot_positive CHECK (staff_slot_number > 0)
);

-- FCFS Guarantee: Only one SELECTED status per subject
CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_selected 
ON subject_selection(subject_id) 
WHERE status = 'SELECTED';

COMMENT ON INDEX uq_subject_selected IS 'CRITICAL DO NOT DROP: Enforces FCFS guarantee - only one SELECTED status per subject';

-- Slot Integrity: Unique slot per staff per window
CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_slot_per_window 
ON subject_selection(staff_id, window_id, staff_slot_number) 
WHERE status = 'SELECTED';

COMMENT ON INDEX uq_staff_slot_per_window IS 'CRITICAL DO NOT DROP: Enforces slot integrity - unique staff_slot_number per staff per window';

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_subject_selection_window ON subject_selection(window_id);
CREATE INDEX IF NOT EXISTS idx_subject_selection_staff ON subject_selection(staff_id);
CREATE INDEX IF NOT EXISTS idx_subject_selection_status ON subject_selection(status);
CREATE INDEX IF NOT EXISTS idx_subject_selection_subject ON subject_selection(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_selection_staff_window ON subject_selection(staff_id, window_id);

-- ============================================================================
-- TABLE: audit_log
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor_staff_id BIGINT,
    action_type VARCHAR(50) NOT NULL,
    subject_id BIGINT,
    affected_staff_id BIGINT,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_audit_log_actor FOREIGN KEY (actor_staff_id) REFERENCES staff(id) ON DELETE SET NULL,
    CONSTRAINT fk_audit_log_subject FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE SET NULL,
    CONSTRAINT fk_audit_log_affected_staff FOREIGN KEY (affected_staff_id) REFERENCES staff(id) ON DELETE SET NULL,
    CONSTRAINT chk_audit_log_action_type CHECK (action_type IN ('SELECT', 'CHANGE', 'OVERRIDE', 'WINDOW_OPEN', 'WINDOW_CLOSE'))
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor_staff_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_subject ON audit_log(subject_id);

-- ============================================================================
-- AUDIT LOG IMMUTABILITY ENFORCEMENT
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_audit_log_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'UPDATE on audit_log is forbidden - audit log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_audit_log_update
BEFORE UPDATE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_log_update();

CREATE OR REPLACE FUNCTION prevent_audit_log_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'DELETE on audit_log is forbidden - audit log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_audit_log_delete
BEFORE DELETE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_log_delete();

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
