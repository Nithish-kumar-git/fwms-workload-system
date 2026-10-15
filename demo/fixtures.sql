-- SYNTHETIC ONLY. Apply once as schema owner after demo/schema.sql, never at startup.
BEGIN;
DO $$
BEGIN
    IF current_database() NOT IN ('fwms_demo','fwms_demo_test')
       OR NOT EXISTS (SELECT 1 FROM fwms_demo_meta.environment WHERE purpose='synthetic-only' AND schema_version=1)
       OR EXISTS (SELECT 1 FROM public.staff) THEN
        RAISE EXCEPTION 'Refusing fixture load: database must be verified and staff table empty';
    END IF;
END $$;
-- All staff IDs come from BIGSERIAL. Never setval, copy institutional records or assign fixed IDs.
INSERT INTO staff (email,name,emp_code,role,is_coordinator,shift,tch_norm,total_workload_norm)
VALUES ('synthetic-alpha@demo.example.com','Synthetic Faculty Alpha','SYN101','faculty',false,'SHIFT1',16,16),
       ('synthetic-beta@demo.example.com','Synthetic Faculty Beta','SYN102','faculty',false,'SHIFT1',16,16);
INSERT INTO batch(name) VALUES ('Synthetic Demo Batch');
INSERT INTO specialization(name) VALUES ('Synthetic Computing');
INSERT INTO program(name,ug_pg) VALUES ('Demo Computing Department','UG');
INSERT INTO semester(label,state) VALUES ('I','CLOSED'),('II','OPEN'),('III','CLOSED'),('IV','CLOSED'),('V','CLOSED'),('VI','CLOSED');
INSERT INTO section(label,student_strength,shift) VALUES ('A',20,1);
INSERT INTO academic_year(name,start_date,end_date) VALUES ('2026-2027','2026-06-01','2027-05-31');
INSERT INTO cycle(academic_year_id,semester_id,status,opened_at)
SELECT ay.id,s.id,'OPEN',now() FROM academic_year ay CROSS JOIN semester s WHERE s.label='II';
INSERT INTO subject(code,name,l,t,p,credits,tch,course_category,course_type,curriculum_year)
VALUES ('SYN-CS101','Synthetic Algorithms',3,1,0,4,4,'PC','THEORY','2022'),
       ('SYN-CS102','Synthetic Database Lab',0,0,4,2,4,'PC','LAB','2022');
INSERT INTO subject_offering(subject_id,program_id,semester_id,section_id,shift,student_strength,academic_year,academic_year_id)
SELECT sub.id,p.id,sem.id,sec.id,1,20,ay.name,ay.id
FROM subject sub CROSS JOIN program p CROSS JOIN semester sem CROSS JOIN section sec CROSS JOIN academic_year ay
WHERE sem.label='II';
INSERT INTO faculty_preference(staff_id,subject_offering_id,preference_number,cycle_id,old_academic_cycle_id)
SELECT st.id,so.id,1,c.id,c.id FROM staff st CROSS JOIN subject_offering so
JOIN subject sub ON sub.id=so.subject_id JOIN cycle c ON c.semester_id=so.semester_id
WHERE st.emp_code='SYN101' AND sub.code='SYN-CS101';
INSERT INTO allocation(staff_id,subject_offering_id,l_assigned,t_assigned,p_assigned,cycle_id,old_academic_cycle_id)
SELECT st.id,so.id,3,1,0,c.id,c.id FROM staff st CROSS JOIN subject_offering so
JOIN subject sub ON sub.id=so.subject_id JOIN cycle c ON c.semester_id=so.semester_id
WHERE st.emp_code='SYN101' AND sub.code='SYN-CS101';
INSERT INTO workload_summary(staff_id,academic_year,semester_type,tch_total,norm_hours,deviation_hours,total_workload,cycle_id)
SELECT st.id,ay.name,'EVEN',4,16,-12,4,c.id FROM staff st CROSS JOIN cycle c
JOIN academic_year ay ON ay.id=c.academic_year_id WHERE st.emp_code='SYN101';
-- Three login identities are created atomically on demand by /auth/demo-login.
COMMIT;
