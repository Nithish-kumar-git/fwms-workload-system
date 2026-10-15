-- ONE-TIME SETUP FOR A NEW DEDICATED DEMO INSTANCE ONLY. Never run startup.sh.
-- An operator must first create fwms_demo (or fwms_demo_test) and its app role.
BEGIN;
-- Preflight uses only trusted catalogs, never an operator's $user/search_path.
SET LOCAL search_path = pg_catalog, pg_temp;
DO $$
BEGIN
    IF current_database() NOT IN ('fwms_demo', 'fwms_demo_test') THEN
        RAISE EXCEPTION 'Refusing non-demo database';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables
               WHERE schemaname NOT IN ('pg_catalog', 'information_schema')) THEN
        RAISE EXCEPTION 'Refusing non-empty database; do not reuse an institutional database';
    END IF;
    -- Safe defaults: trusted PostgreSQL system schemas, an EMPTY public schema,
    -- and the built-in plpgsql extension/languages. No wildcard pg_* exemptions,
    -- temporary schemas, provider extensions or pre-existing demo marker schema.
    -- Unexpected Neon defaults require review, not automatic deletion/allowlisting.
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = 'public')
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_namespace
                  WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')) THEN
        RAISE EXCEPTION 'Refusing missing public schema or unexpected pre-existing schema';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT relnamespace AS namespace FROM pg_catalog.pg_class
            UNION ALL SELECT pronamespace FROM pg_catalog.pg_proc
            UNION ALL SELECT typnamespace FROM pg_catalog.pg_type
            UNION ALL SELECT collnamespace FROM pg_catalog.pg_collation
            UNION ALL SELECT connamespace FROM pg_catalog.pg_constraint
            UNION ALL SELECT oprnamespace FROM pg_catalog.pg_operator
            UNION ALL SELECT opcnamespace FROM pg_catalog.pg_opclass
            UNION ALL SELECT opfnamespace FROM pg_catalog.pg_opfamily
            UNION ALL SELECT connamespace FROM pg_catalog.pg_conversion
            UNION ALL SELECT stxnamespace FROM pg_catalog.pg_statistic_ext
            UNION ALL SELECT cfgnamespace FROM pg_catalog.pg_ts_config
            UNION ALL SELECT dictnamespace FROM pg_catalog.pg_ts_dict
            UNION ALL SELECT prsnamespace FROM pg_catalog.pg_ts_parser
            UNION ALL SELECT tmplnamespace FROM pg_catalog.pg_ts_template
        ) AS objects
        JOIN pg_catalog.pg_namespace AS schemas ON schemas.oid = objects.namespace
        WHERE schemas.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    ) THEN
        RAISE EXCEPTION 'Refusing pre-existing relations, routines, types or other schema objects';
    END IF;
    -- These database objects have no schema namespace, but can affect setup.
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_extension
               WHERE extname <> 'plpgsql' OR extnamespace <> 'pg_catalog'::regnamespace)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_language
                  WHERE lanname NOT IN ('internal', 'c', 'sql', 'plpgsql'))
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_event_trigger)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_data_wrapper)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_server)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_publication)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_subscription
                  WHERE subdbid = (SELECT oid FROM pg_catalog.pg_database
                                   WHERE datname = current_database()))
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_largeobject_metadata)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_transform)
       OR EXISTS (
           SELECT 1 FROM pg_catalog.pg_default_acl AS defaults
           LEFT JOIN pg_catalog.pg_roles AS grantors ON grantors.oid = defaults.defaclrole
           LEFT JOIN pg_catalog.pg_namespace AS schemas ON schemas.oid = defaults.defaclnamespace
           -- Only the two reviewed Neon public defaults are permitted, unchanged.
           -- Match default-owner plus ACL grantee, grantor and all grant options.
           -- Text comparison avoids resolving absent Neon roles on local PostgreSQL.
           WHERE NOT COALESCE(
               current_database() = 'fwms_demo'
               AND grantors.rolname = 'cloud_admin' AND schemas.nspname = 'public'
               AND ((defaults.defaclobjtype = 'S'
                     AND defaults.defaclacl::text = '{neon_superuser=r*w*U*/cloud_admin}')
                    OR (defaults.defaclobjtype = 'r'
                        AND defaults.defaclacl::text = '{neon_superuser=a*r*w*d*D*m*/cloud_admin}')),
               false)
       ) THEN
        RAISE EXCEPTION 'Refusing unexpected extensions or other pre-existing database objects';
    END IF;
END $$;

-- All unqualified application objects must be created in public. pg_catalog is
-- implicitly searched first; pg_temp is explicitly last to prevent temp shadowing.
-- Provision only in a quiescent database with no concurrent schema writers.
SET LOCAL search_path = public, pg_temp;
CREATE SCHEMA fwms_demo_meta;
CREATE TABLE fwms_demo_meta.environment (
    singleton boolean PRIMARY KEY CHECK (singleton),
    purpose text NOT NULL CHECK (purpose = 'synthetic-only'),
    schema_version integer NOT NULL CHECK (schema_version = 1)
);
INSERT INTO fwms_demo_meta.environment VALUES (true, 'synthetic-only', 1);

CREATE TABLE staff (
    id BIGSERIAL PRIMARY KEY, email varchar(255) NOT NULL UNIQUE,
    name varchar(255) NOT NULL, emp_code varchar(20) UNIQUE,
    role varchar(50) NOT NULL DEFAULT 'faculty' CHECK (role IN ('hod','tt_coordinator','faculty')),
    is_coordinator boolean NOT NULL DEFAULT false, is_active boolean NOT NULL DEFAULT true,
    designation varchar(50) DEFAULT 'Assistant Professor', shift varchar(20) DEFAULT 'SHIFT1',
    tch_norm integer DEFAULT 16, total_workload_norm integer DEFAULT 16,
    is_class_teacher boolean NOT NULL DEFAULT false,
    ct_program varchar(100), ct_section varchar(10), ct_semester varchar(10),
    ct_shift integer, ct_curriculum_year varchar(20),
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (email = 'demo@fwms-demo.com' OR email LIKE '%@demo.example.com')
);
CREATE TABLE batch (id BIGSERIAL PRIMARY KEY, name varchar(255) NOT NULL UNIQUE,
                    is_active boolean NOT NULL DEFAULT true, created_at timestamptz DEFAULT now());
CREATE TABLE specialization (id BIGSERIAL PRIMARY KEY, name varchar(255) NOT NULL UNIQUE,
                    is_active boolean NOT NULL DEFAULT true, created_at timestamptz DEFAULT now());
CREATE TABLE staff_assignment (
    id BIGSERIAL PRIMARY KEY, staff_id bigint REFERENCES staff(id),
    batch_id bigint REFERENCES batch(id), specialization_id bigint REFERENCES specialization(id),
    created_at timestamptz DEFAULT now(), UNIQUE (staff_id,batch_id,specialization_id)
);
CREATE TABLE program (id BIGSERIAL PRIMARY KEY, name varchar(100) NOT NULL UNIQUE,
    ug_pg varchar(5) NOT NULL CHECK (ug_pg IN ('UG','PG')), is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now());
CREATE TABLE semester (
    id BIGSERIAL PRIMARY KEY, label varchar(10) NOT NULL UNIQUE,
    program_id bigint REFERENCES program(id), state varchar(20) NOT NULL DEFAULT 'CLOSED'
    CHECK (state IN ('OPEN','CLOSED','ALLOCATED','FROZEN')),
    opened_at timestamptz, closed_at timestamptz, allocated_at timestamptz, frozen_at timestamptz,
    frozen_by_staff_id bigint REFERENCES staff(id), created_at timestamptz DEFAULT now()
);
CREATE TABLE section (id BIGSERIAL PRIMARY KEY, label varchar(10) NOT NULL,
    student_strength integer, shift integer NOT NULL DEFAULT 1 CHECK (shift IN (1,2)),
    created_at timestamptz DEFAULT now());
CREATE TABLE academic_year (id SERIAL PRIMARY KEY, name varchar(20) NOT NULL UNIQUE,
    start_date date, end_date date, created_at timestamp DEFAULT now());
CREATE TABLE cycle (
    id SERIAL PRIMARY KEY, academic_year_id integer NOT NULL REFERENCES academic_year(id),
    semester_id bigint NOT NULL REFERENCES semester(id),
    status varchar(20) NOT NULL DEFAULT 'CLOSED' CHECK (status IN ('OPEN','CLOSED','ALLOCATED','FROZEN')),
    opened_at timestamp, closed_at timestamp, allocated_at timestamp, frozen_at timestamp,
    frozen_by_staff_id bigint REFERENCES staff(id), created_at timestamp DEFAULT now(),
    UNIQUE (academic_year_id,semester_id)
);
CREATE TABLE subject (
    id BIGSERIAL PRIMARY KEY, code varchar(50) NOT NULL UNIQUE, name varchar(255) NOT NULL,
    batch_id bigint REFERENCES batch(id), specialization_id bigint REFERENCES specialization(id),
    is_active boolean NOT NULL DEFAULT true, l integer, t integer, p integer, credits integer,
    tch integer, course_category varchar(10), course_type varchar(10), curriculum_year varchar(20),
    created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now(),
    UNIQUE (id,batch_id,specialization_id)
);
CREATE TABLE subject_offering (
    id BIGSERIAL PRIMARY KEY, subject_id bigint NOT NULL REFERENCES subject(id),
    program_id bigint NOT NULL REFERENCES program(id), semester_id bigint NOT NULL REFERENCES semester(id),
    section_id bigint NOT NULL REFERENCES section(id), shift integer NOT NULL CHECK (shift IN (1,2)),
    student_strength integer, academic_year varchar(20) NOT NULL,
    academic_year_id integer NOT NULL REFERENCES academic_year(id), old_academic_cycle_id integer,
    is_active boolean NOT NULL DEFAULT true, created_at timestamptz DEFAULT now(),
    UNIQUE (subject_id,program_id,semester_id,section_id,shift,academic_year_id)
);
CREATE TABLE selection_window (
    id BIGSERIAL PRIMARY KEY, name varchar(255) NOT NULL, start_time timestamptz NOT NULL,
    end_time timestamptz NOT NULL CHECK (end_time > start_time), max_subjects_per_staff integer NOT NULL
    CHECK (max_subjects_per_staff > 0), is_active boolean NOT NULL DEFAULT true,
    status varchar(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','SCHEDULED','OPEN','CLOSED','ARCHIVED')),
    batch_id bigint NOT NULL REFERENCES batch(id), specialization_id bigint NOT NULL REFERENCES specialization(id),
    allocation_locked boolean NOT NULL DEFAULT false, cycle_id integer REFERENCES cycle(id),
    academic_cycle_id integer, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now()
);
CREATE UNIQUE INDEX uq_one_open_window_per_batch_spec ON selection_window(batch_id,specialization_id)
WHERE status = 'OPEN';
CREATE TABLE subject_selection (
    id BIGSERIAL PRIMARY KEY, subject_id bigint NOT NULL REFERENCES subject(id),
    staff_id bigint NOT NULL REFERENCES staff(id), batch_id bigint NOT NULL REFERENCES batch(id),
    specialization_id bigint NOT NULL REFERENCES specialization(id), window_id bigint NOT NULL REFERENCES selection_window(id),
    staff_slot_number integer NOT NULL CHECK (staff_slot_number > 0),
    status varchar(20) NOT NULL CHECK (status IN ('SELECTED','OVERRIDDEN')),
    selected_at timestamptz DEFAULT now(), created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now(),
    FOREIGN KEY (subject_id,batch_id,specialization_id) REFERENCES subject(id,batch_id,specialization_id),
    FOREIGN KEY (staff_id,batch_id,specialization_id) REFERENCES staff_assignment(staff_id,batch_id,specialization_id)
);
CREATE UNIQUE INDEX uq_subject_selected ON subject_selection(subject_id) WHERE status='SELECTED';
CREATE UNIQUE INDEX uq_staff_slot_per_window ON subject_selection(staff_id,window_id,staff_slot_number) WHERE status='SELECTED';
CREATE TABLE faculty_role (id BIGSERIAL PRIMARY KEY, staff_id bigint NOT NULL REFERENCES staff(id),
    role_name varchar(100) NOT NULL, deduction_hours integer, created_at timestamptz DEFAULT now());
CREATE TABLE faculty_preference (
    id BIGSERIAL PRIMARY KEY, staff_id bigint NOT NULL REFERENCES staff(id),
    subject_offering_id bigint NOT NULL REFERENCES subject_offering(id),
    preference_number integer NOT NULL CHECK (preference_number BETWEEN 1 AND 5),
    cycle_id integer NOT NULL REFERENCES cycle(id), old_academic_cycle_id integer,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (staff_id,preference_number,cycle_id), UNIQUE (subject_offering_id,preference_number,cycle_id)
);
CREATE TABLE allocation (
    id BIGSERIAL PRIMARY KEY, staff_id bigint NOT NULL REFERENCES staff(id),
    subject_offering_id bigint NOT NULL REFERENCES subject_offering(id), cycle_id integer NOT NULL REFERENCES cycle(id),
    old_academic_cycle_id integer, l_assigned integer NOT NULL DEFAULT 0 CHECK (l_assigned>=0),
    t_assigned integer NOT NULL DEFAULT 0 CHECK (t_assigned>=0), p_assigned integer NOT NULL DEFAULT 0 CHECK (p_assigned>=0),
    ltp_total integer GENERATED ALWAYS AS (l_assigned+t_assigned+p_assigned) STORED,
    complexity varchar(20), allocated_at timestamptz DEFAULT now(), created_at timestamptz DEFAULT now(),
    UNIQUE(staff_id,subject_offering_id,cycle_id)
);
CREATE TABLE workload_summary (
    id BIGSERIAL PRIMARY KEY, staff_id bigint NOT NULL REFERENCES staff(id),
    academic_year varchar(20) NOT NULL, semester_type varchar(10) NOT NULL CHECK (semester_type IN ('ODD','EVEN')),
    cycle_id integer REFERENCES cycle(id), academic_cycle_id integer, old_academic_cycle_id integer,
    tch_total integer DEFAULT 0, norm_hours integer DEFAULT 0, deviation_hours integer DEFAULT 0,
    total_workload integer DEFAULT 0, other_academic integer DEFAULT 0, research_scholars integer,
    remarks text, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now(),
    UNIQUE(staff_id,academic_year,semester_type)
);
CREATE TABLE workload_snapshot (
    id BIGSERIAL PRIMARY KEY, academic_year varchar(20) NOT NULL, semester_id bigint NOT NULL REFERENCES semester(id),
    approved_by bigint NOT NULL REFERENCES staff(id), snapshot_data jsonb NOT NULL,
    created_at timestamptz DEFAULT now(), UNIQUE(academic_year,semester_id)
);
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY, actor_staff_id bigint REFERENCES staff(id), action_type varchar(50) NOT NULL,
    subject_id bigint REFERENCES subject(id), affected_staff_id bigint REFERENCES staff(id),
    details jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION prevent_demo_immutable_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Append-only demo record'; END $$;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_demo_immutable_mutation();
CREATE TRIGGER snapshot_immutable BEFORE UPDATE OR DELETE ON workload_snapshot
FOR EACH ROW EXECUTE FUNCTION prevent_demo_immutable_mutation();
CREATE FUNCTION prevent_demo_window_time_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status <> 'DRAFT' AND (NEW.start_time IS DISTINCT FROM OLD.start_time
                                 OR NEW.end_time IS DISTINCT FROM OLD.end_time) THEN
        RAISE EXCEPTION 'Window times are immutable after scheduling';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER window_time_immutable BEFORE UPDATE ON selection_window
FOR EACH ROW EXECUTE FUNCTION prevent_demo_window_time_update();
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA fwms_demo_meta FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public,fwms_demo_meta FROM PUBLIC;
-- Grant only to the dedicated app role already provisioned by the operator.
DO $$
DECLARE app_role text;
BEGIN
    app_role := CASE current_database() WHEN 'fwms_demo' THEN 'fwms_demo_runtime' ELSE 'fwms_demo_test_app' END;
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I',current_database(),app_role);
    EXECUTE format('GRANT USAGE ON SCHEMA public,fwms_demo_meta TO %I',app_role);
    EXECUTE format('GRANT SELECT ON fwms_demo_meta.environment TO %I',app_role);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO %I',app_role);
    EXECUTE format('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO %I',app_role);
END $$;
COMMIT;
