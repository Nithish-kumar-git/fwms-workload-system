"""Offline containment regressions. Real ASGI/JWT and SQLite transactions only.

Run independently: python -B tests/verify_security_repairs.py -v
PostgreSQL locking, catalogs and provider behavior are NOT tested here.
"""
from contextlib import contextmanager
import importlib
import io
import logging
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Reuse the established network/.env blockers and synthetic configuration.
from demo import verify_offline as offline
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

engine = None
statements = []
fail_on = None
commits = 0


class TestSession(Session):
    def execute(self, statement, params=None, **kwargs):
        sql = str(statement)
        normalized = ' '.join(sql.split())
        statements.append(normalized)
        if fail_on and fail_on in normalized:
            raise RuntimeError('Injected transaction failure')
        # These are explicit SQLite adapters, not PostgreSQL verification.
        sql = sql.replace(' FOR UPDATE OF c, sem', '').replace('now()', 'CURRENT_TIMESTAMP')
        if 'pg_advisory_xact_lock' in sql:
            # Syntax adapter only. Concurrency is tested separately on PostgreSQL.
            sql, params = 'SELECT 1', {}
        return super().execute(text(sql), params or {}, **kwargs)

    def commit(self):
        global commits
        if fail_on == 'COMMIT':
            raise RuntimeError('Injected commit failure')
        commits += 1
        return super().commit()


@contextmanager
def transaction(*args, **kwargs):
    with TestSession(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


sys.modules['app.db.session'].get_transaction = transaction
from app.main import create_app
from app.allocation import service
from app.auth.dependencies import get_current_coordinator_id, get_current_hod_id
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

SCHEMA = """
CREATE TABLE staff (id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, role TEXT,
 emp_code TEXT, is_active BOOLEAN, is_coordinator BOOLEAN, designation TEXT, shift TEXT,
 tch_norm INTEGER, is_class_teacher BOOLEAN, ct_program TEXT, ct_section TEXT,
 ct_semester TEXT, ct_shift INTEGER);
CREATE TABLE academic_year (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE semester (id INTEGER PRIMARY KEY, label TEXT, state TEXT, allocated_at TEXT);
CREATE TABLE cycle (id INTEGER PRIMARY KEY, academic_year_id INTEGER, semester_id INTEGER, status TEXT);
CREATE TABLE program (id INTEGER PRIMARY KEY, name TEXT, is_active BOOLEAN);
CREATE TABLE section (id INTEGER PRIMARY KEY, label TEXT);
CREATE TABLE subject (id INTEGER PRIMARY KEY, code TEXT, name TEXT, tch INTEGER, l INTEGER, t INTEGER, p INTEGER);
CREATE TABLE subject_offering (id INTEGER PRIMARY KEY, subject_id INTEGER, program_id INTEGER,
 semester_id INTEGER, section_id INTEGER, shift INTEGER, academic_year_id INTEGER, is_active BOOLEAN);
CREATE TABLE faculty_preference (id INTEGER PRIMARY KEY, staff_id INTEGER, subject_offering_id INTEGER,
 preference_number INTEGER, cycle_id INTEGER, submitted_at TEXT);
CREATE TABLE allocation (id INTEGER PRIMARY KEY, staff_id INTEGER, subject_offering_id INTEGER,
 l_assigned INTEGER, t_assigned INTEGER, p_assigned INTEGER, cycle_id INTEGER, old_academic_cycle_id INTEGER);
CREATE TABLE workload_summary (id INTEGER PRIMARY KEY, staff_id INTEGER, academic_year TEXT, semester_type TEXT,
 tch_total INTEGER, norm_hours INTEGER, deviation_hours INTEGER, total_workload INTEGER, cycle_id INTEGER,
 old_academic_cycle_id INTEGER, updated_at TEXT, UNIQUE(staff_id,academic_year,semester_type));
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, actor_staff_id INTEGER, action_type TEXT, details TEXT);
"""

SEED = """
INSERT INTO staff VALUES
 (1,'hod@demo.example.com','Synthetic HOD','hod','HOD',1,1,'Professor','SHIFT1',16,0,NULL,NULL,NULL,NULL),
 (2,'coord@demo.example.com','Synthetic Coordinator','tt_coordinator','COORD',1,1,'Professor','SHIFT1',16,0,NULL,NULL,NULL,NULL),
 (3,'teacher@demo.example.com','Synthetic Teacher','faculty','TEACHER',1,0,'Professor','SHIFT1',16,0,NULL,NULL,NULL,NULL),
 (4,'other@demo.example.com','Synthetic Other','faculty','OTHER',1,0,'Professor','SHIFT1',16,0,NULL,NULL,NULL,NULL);
INSERT INTO academic_year VALUES (1,'2026-2027'),(2,'2025-2026');
INSERT INTO semester VALUES (1,'I','CLOSED',NULL),(2,'II','OPEN',NULL),(4,'IV','OPEN',NULL),(6,'VI','FROZEN','old');
INSERT INTO cycle VALUES (11,1,2,'OPEN'),(12,1,4,'OPEN'),(13,1,6,'FROZEN'),(14,2,2,'CLOSED');
INSERT INTO program VALUES (1,'Synthetic Computing',1),(2,'Synthetic Engineering',1),(3,'Inactive',0);
INSERT INTO section VALUES (1,'A');
INSERT INTO subject VALUES (1,'SYN1','Synthetic Algorithms',4,3,1,0),(2,'SYN2','Synthetic Databases',4,3,1,0);
INSERT INTO subject_offering VALUES
 (201,1,1,2,1,1,1,1),(202,2,2,2,1,1,1,1),(203,1,1,4,1,1,1,1),
 (204,1,1,6,1,1,1,1),(205,1,1,2,1,1,2,1);
INSERT INTO faculty_preference VALUES
 (1,3,201,1,11,'2026-01-01'),(2,4,202,1,11,'2026-01-01'),
 (3,3,203,1,12,'2026-01-01'),(4,4,201,1,14,'2025-01-01');
INSERT INTO allocation VALUES
 (101,3,201,3,1,0,11,11),(102,4,202,3,1,0,11,11),(103,3,203,3,1,0,12,12),
 (104,3,204,3,1,0,13,13),(105,3,205,3,1,0,14,14),(106,4,201,3,1,0,14,14);
"""


class RepairsTests(unittest.TestCase):
    def setUp(self):
        global engine, statements, fail_on, commits
        engine = create_engine('sqlite://', poolclass=StaticPool,
                               connect_args={'check_same_thread': False})
        offline._test_engine = engine
        with engine.begin() as conn:
            for command in (SCHEMA + SEED).split(';'):
                if command.strip():
                    conn.execute(text(command))
        statements, fail_on, commits = [], None, 0
        self.app = create_app()
        # No lifespan/server startup and no production engine.
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        engine.dispose()

    def headers(self, role='tt_coordinator'):
        sid = {'hod': 1, 'tt_coordinator': 2, 'faculty': 3}[role]
        token = offline.jwt_utils.create_jwt(sid, role+'@demo.example.com', role, role)
        return {'Authorization': 'Bearer '+token}

    def rows(self, table):
        with engine.connect() as conn:
            return [tuple(row) for row in conn.execute(text('SELECT * FROM '+table+' ORDER BY id'))]

    def snapshot(self):
        return {table: self.rows(table) for table in
                ('allocation','workload_summary','semester','cycle','audit_log','staff','subject_offering')}

    def assert_no_writes(self):
        self.assertFalse([sql for sql in statements if sql.split()[0] in ('INSERT','UPDATE','DELETE')])

    def test_every_served_administrative_mutation_has_existing_role_guard(self):
        prefixes = ('/api/admin','/api/cycles','/api/semester','/api/windows',
                    '/api/pref-window','/api/allocation','/api/coordinator',
                    '/api/curriculum','/api/subjects','/api/reports')
        before = self.snapshot()
        count = 0
        for route in self.app.routes:
            if not isinstance(route, APIRoute) or not route.path.startswith(prefixes):
                continue
            for method in route.methods & {'POST','PUT','PATCH','DELETE'}:
                guards = {dep.call for dep in route.dependant.dependencies}
                self.assertTrue(guards & {get_current_coordinator_id, get_current_hod_id}, route.path)
                path = route.path
                for param in route.param_convertors:
                    path = path.replace('{'+param+'}', '999')
                for role, expected in ((None,401),('faculty',403)):
                    response = self.client.request(method,path,json={},headers=self.headers(role) if role else {})
                    self.assertEqual(response.status_code,expected,(method,path,role))
                if get_current_hod_id in guards:
                    response = self.client.request(method,path,json={},headers=self.headers())
                    self.assertEqual(response.status_code,403,(method,path))
                count += 1
        self.assertGreater(count, 30)
        self.assert_no_writes()
        self.assertEqual(self.snapshot(),before)

    def test_maintenance_routes_absent_from_openapi_and_return_404_even_to_hod(self):
        from app.reports.router import maintenance_router
        schema = self.app.openapi()['paths']
        for route in maintenance_router.routes:
            self.assertNotIn(route.path,schema)
            path = route.path.replace('{emp_code}','SYN')
            for method in route.methods:
                for headers in ({},self.headers('hod')):
                    response=self.client.request(method,path,headers=headers)
                    self.assertEqual(response.status_code,404,(method,path))
        self.assert_no_writes()

    def test_staff_diagnostics_require_hod(self):
        for path in ('/api/admin/staff/list-debug','/api/admin/staff/debug-role-ct'):
            for role,expected in ((None,401),('faculty',403),('tt_coordinator',403)):
                self.assertEqual(self.client.get(path,headers=self.headers(role) if role else {}).status_code,expected)
        self.assert_no_writes()

    def test_empty_requests_do_not_open_allocation_transaction(self):
        before=self.snapshot()
        for payload in (None,{}, {'program_id':1}):
            response=self.client.post('/api/allocation/run',json=payload,headers=self.headers())
            self.assertEqual(response.status_code,400)
        with patch.object(service,'workload_transaction',side_effect=AssertionError('No transaction expected')):
            self.assertFalse(service.run_allocation()['success'])
        self.assert_no_writes()
        self.assertEqual(self.snapshot(),before)

    def test_invalid_scope_and_frozen_state_never_write(self):
        for scope in ({'semester_id':999},{'semester_id':2,'academic_year':'2025-2026'},
                      {'semester_id':2,'program_id':999},{'semester_id':2,'program_id':3},
                      {'semester_id':6},{'academic_year':'missing'}):
            with self.subTest(scope=scope):
                before=self.snapshot()
                self.assertFalse(service.run_allocation(**scope)['success'])
                self.assert_no_writes()
                self.assertEqual(self.snapshot(),before)

    def test_no_preferences_or_no_offerings_rejected_before_cleanup(self):
        with engine.begin() as conn:
            conn.execute(text('DELETE FROM faculty_preference WHERE cycle_id=11'))
        before=self.snapshot()
        self.assertFalse(service.run_allocation(semester_id=2)['success'])
        self.assert_no_writes()
        self.assertEqual(self.snapshot(),before)
        with engine.begin() as conn:
            conn.execute(text('UPDATE subject_offering SET is_active=false WHERE semester_id=2'))
        self.assertFalse(service.run_allocation(semester_id=2)['success'])
        self.assert_no_writes()

    def test_success_preserves_unrelated_semesters_cycles_and_historical_allocations(self):
        untouched=[row for row in self.rows('allocation') if row[6]!=11]
        result=service.run_allocation(semester_id=2,academic_year='2026-2027')
        self.assertTrue(result['success'])
        self.assertEqual(result['subjects_assigned'],2)
        self.assertEqual([row for row in self.rows('allocation') if row[6]!=11],untouched)
        self.assertEqual({row[0]:row[2] for row in self.rows('semester')},
                         {1:'CLOSED',2:'ALLOCATED',4:'OPEN',6:'FROZEN'})
        self.assertEqual({row[0]:row[3] for row in self.rows('cycle')},
                         {11:'ALLOCATED',12:'OPEN',13:'FROZEN',14:'CLOSED'})
        self.assertEqual(commits,1)

    def test_program_scope_preserves_other_program_and_uses_its_capacity(self):
        # Same teacher already has four hours in another program in this semester.
        with engine.begin() as conn:
            conn.execute(text('UPDATE allocation SET staff_id=3 WHERE id=102'))
            conn.execute(text('UPDATE staff SET tch_norm=4 WHERE id=3'))
        original=self.rows('allocation')
        result=service.run_allocation(semester_id=2,program_id=1)
        self.assertTrue(result['success'])
        self.assertEqual([row for row in self.rows('allocation') if row[0]==102],
                         [row for row in original if row[0]==102])
        self.assertFalse(any(a['staff_id']==3 for a in result['allocations']))
        self.assertEqual(result['subjects_total'],1)

    def test_programs_can_run_in_sequence_until_explicit_full_finalization(self):
        first=service.run_allocation(semester_id=2,program_id=1)
        self.assertTrue(first['success'])
        retained=[row for row in self.rows('allocation') if row[2]==201 and row[6]==11]
        second=service.run_allocation(semester_id=2,program_id=2)
        self.assertTrue(second['success'])
        self.assertEqual([row for row in self.rows('allocation') if row[2]==201 and row[6]==11],retained)
        self.assertEqual(next(row for row in self.rows('semester') if row[0]==2)[2],'OPEN')
        self.assertEqual(next(row for row in self.rows('cycle') if row[0]==11)[3],'OPEN')
        self.assertTrue(service.run_allocation(semester_id=2)['success'])
        self.assertEqual(next(row for row in self.rows('cycle') if row[0]==11)[3],'ALLOCATED')

    def test_single_program_scope_still_finalizes_whole_semester(self):
        result=service.run_allocation(semester_id=4,program_id=1)
        self.assertTrue(result['success'])
        self.assertEqual(next(row for row in self.rows('cycle') if row[0]==12)[3],'ALLOCATED')

    def test_ranking_and_fallback_are_preserved(self):
        result=service.run_allocation(semester_id=2)
        self.assertEqual({a['subject_offering_id']:(a['staff_id'],a['allocation_stage'])
                          for a in result['allocations']}, {201:(3,'PREF_1'),202:(4,'PREF_1')})
        # The preference from another cycle must not win the earlier timestamp.
        self.assertEqual(result['allocations'][0]['staff_id'],3)

    def test_lower_rank_and_final_pass_still_allocate(self):
        with engine.begin() as conn:
            conn.execute(text('UPDATE faculty_preference SET preference_number=2 WHERE id=1'))
            conn.execute(text('DELETE FROM faculty_preference WHERE id=2'))
        result=service.run_allocation(semester_id=2)
        self.assertEqual(result['subjects_assigned'],2)
        stages={a['subject_offering_id']:a['allocation_stage'] for a in result['allocations']}
        self.assertEqual(stages[201],'PREF_2')
        self.assertTrue(stages[202].startswith('FINAL_PASS'))

    def test_final_pass_remains_skipped_when_no_preference_can_be_allocated(self):
        with engine.begin() as conn:
            conn.execute(text('UPDATE staff SET tch_norm=0'))
        result=service.run_allocation(semester_id=2)
        self.assertTrue(result['success'])
        self.assertEqual(result['subjects_assigned'],0)
        self.assertEqual(result['subjects_unassigned'],2)

    def test_shared_workload_bucket_retains_other_even_semester_contributions(self):
        result=service.run_allocation(semester_id=2)
        teacher=next(w for w in result['workload_summary'] if w['staff_id']==3)
        self.assertEqual(teacher['tch_assigned'],12)  # II + IV + frozen VI, same year

    def test_failure_during_insert_audit_status_or_commit_rolls_back_all(self):
        global fail_on
        for stage in ('INSERT INTO allocation','INSERT INTO workload_summary','INSERT INTO audit_log',
                      'UPDATE semester','UPDATE cycle','COMMIT'):
            with self.subTest(stage=stage):
                before=self.snapshot()
                fail_on=stage
                with self.assertRaises(RuntimeError):
                    service.run_allocation(semester_id=2)
                self.assertEqual(self.snapshot(),before)
                fail_on=None

    def test_batch_validates_all_scopes_before_first_write(self):
        with engine.begin() as conn:
            conn.execute(text("UPDATE semester SET state='FROZEN' WHERE id=4"))
        before=self.snapshot()
        self.assertFalse(service.run_all_open_semesters()['success'])
        self.assert_no_writes()
        self.assertEqual(self.snapshot(),before)

    def test_batch_success_only_updates_its_selected_cycles(self):
        result=service.run_all_open_semesters()
        self.assertTrue(result['success'])
        self.assertEqual([r['semester_id'] for r in result['results']],[2,4])
        self.assertEqual(commits,1)
        self.assertEqual(next(row for row in self.rows('semester') if row[0]==6)[2],'FROZEN')
        self.assertEqual(next(row for row in self.rows('semester') if row[0]==1)[2],'CLOSED')

    def test_failure_in_second_semester_rolls_back_first_semester_too(self):
        original=service._allocate_in_transaction
        def allocate(session,scope,program_id=None):
            if scope['semester_id']==4:
                raise RuntimeError('Injected second-semester failure')
            return original(session,scope,program_id)
        before=self.snapshot()
        with patch.object(service,'_allocate_in_transaction',side_effect=allocate):
            response=self.client.post('/api/allocation/run-all',headers=self.headers())
        self.assertEqual(response.status_code,500)
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(commits,0)

    def test_authorized_coordinator_and_hod_can_allocate(self):
        response=self.client.post('/api/allocation/run',json={'semester_id':2},headers=self.headers())
        self.assertEqual(response.status_code,200)
        response=self.client.post('/api/allocation/run',json={'semester_id':4},headers=self.headers('hod'))
        self.assertEqual(response.status_code,200)


class StartupTests(unittest.TestCase):
    def test_actual_institutional_startup_does_not_query_or_mutate_database(self):
        import asyncio
        import app.main as main_module
        with patch.object(main_module.settings,'DEMO_MODE',False), \
             patch.object(main_module,'configure_logging'), \
             patch('app.db.session.get_transaction',side_effect=AssertionError('Startup SQL forbidden')):
            asyncio.run(main_module.startup_event())

    def test_serving_entrypoints_do_not_run_provisioning(self):
        startup=(ROOT/'startup.sh').read_text(encoding='utf-8-sig')
        self.assertIn('exec python -B -m app.start_backend',startup)
        self.assertNotIn('DATABASE_URL',startup)
        self.assertNotIn('psql',startup)
        compose=(ROOT/'docker-compose.yml').read_text()
        self.assertIn('command: ["sh", "startup.sh"]',compose)
        self.assertNotIn('psql ',compose)
        docker=(ROOT/'Dockerfile').read_text()
        self.assertNotIn('COPY migrations/',docker)
        self.assertIn('/api/health',docker)
        batch=(ROOT/'run_migrations.bat').read_text()
        self.assertNotIn('postgresql://',batch)
        self.assertIn('exit /b 1',batch)
        self.assertNotIn('/docker-entrypoint-initdb.d/',(ROOT/'docker-compose.prod.yml').read_text())
        import yaml
        production=yaml.safe_load((ROOT/'docker-compose.prod.yml').read_text())['services']['app']
        self.assertEqual(production['command'],['sh','startup.sh'])
        self.assertIn('/api/health',str(production['healthcheck']))
        self.assertNotIn('--access-log',str(production))

    def test_native_launcher_only_runs_server_and_passes_port(self):
        from app import start_backend
        fake_app=types.ModuleType('app.main'); fake_app.app=object()
        server=types.ModuleType('uvicorn'); server.run=Mock()
        with patch.dict(os.environ,{'FWMS_DEMO_MODE':'false','PORT':'8123'},clear=True), \
             patch.dict(sys.modules,{'app.main':fake_app,'uvicorn':server}):
            self.assertEqual(start_backend.main(),0)
        args,kwargs=server.run.call_args
        self.assertIs(args[0],fake_app.app)
        self.assertEqual(kwargs['port'],8123)
        self.assertEqual(kwargs['host'],'0.0.0.0')

    def test_launcher_refuses_demo_mode_and_invalid_port_without_echoing_env(self):
        from app import start_backend
        from contextlib import redirect_stderr
        for env in ({'FWMS_DEMO_MODE':'true'},{'PORT':'not-a-port'},{'PORT':'0'}):
            output=io.StringIO()
            with patch.dict(os.environ,env,clear=True),redirect_stderr(output):
                self.assertEqual(start_backend.main(),1)
            self.assertNotIn('not-a-port',output.getvalue())

    def test_logs_redact_formatted_exceptions_json_and_credentials(self):
        from app.core.log_redaction import RedactingFormatter
        from app.core.logging_config import JSONFormatter
        secrets=('synthetic-secret-0123456789', 'postgresql://synthetic:private@invalid/fwms')
        try:
            raise ValueError(secrets[1])
        except ValueError:
            record=logging.LogRecord('test',logging.ERROR,__file__,1,'%s',(secrets[0],),sys.exc_info())
        record.extra={'credential':secrets[0]}
        for delegate in (logging.Formatter(),JSONFormatter()):
            output=RedactingFormatter(delegate,secrets).format(record)
            for secret in secrets:
                self.assertNotIn(secret,output)


if __name__=='__main__':
    unittest.main(verbosity=2)
