"""Real PostgreSQL regressions in a new disposable, loopback-only cluster.

Uses existing PostgreSQL binaries; never connects to an existing server, loads
.env, downloads packages, or uses provider/institutional credentials.
Run independently: python -B tests/verify_allocation_postgres.py -v
"""
import builtins
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import io
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OWNER = 'fwms_test_owner'
ROLE = 'fwms_demo_test_app'
DATABASE = 'fwms_demo_test'
SYNTHETIC_SECRET = 'isolated-postgres-regression-signing-key-0123456789'
cluster = None
port = None
pgbin = None
service = snapshot_service = admin_service = engine = None


def run_program(*args):
    # Windows background postgres processes can inherit captured pipe handles;
    # use a file so pg_ctl returning does not wait for the server to exit.
    with tempfile.TemporaryFile() as output:
        result = subprocess.run([str(arg) for arg in args], stdout=output, stderr=output,
                                timeout=60,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError('Local PostgreSQL command failed: '+Path(str(args[0])).name)


def owner_connection(database=DATABASE):
    import psycopg2
    # Every connection is constructed here for this process's own new cluster.
    assert cluster is not None and port is not None
    return psycopg2.connect(host='127.0.0.1', port=port, dbname=database, user=OWNER,
                            connect_timeout=3)


@contextmanager
def owner_sql():
    connection = owner_connection()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    finally:
        connection.close()


def prepare_cluster():
    global cluster, port, pgbin, service, snapshot_service, admin_service, engine
    candidates = [Path(os.environ['FWMS_PG_BIN'])] if os.environ.get('FWMS_PG_BIN') else [
        Path('C:/Program Files/PostgreSQL/18/bin'), Path('C:/Program Files/PostgreSQL/16/bin')]
    pgbin = next((p for p in candidates if (p/'initdb.exe').is_file()), None)
    if pgbin is None:
        raise RuntimeError('Existing PostgreSQL binaries unavailable; integration NOT verified')
    temporary_root = Path(tempfile.gettempdir()).resolve()
    cluster = Path(tempfile.mkdtemp(prefix='fwms-final-pg-')).resolve()
    assert cluster.parent == temporary_root and cluster.name.startswith('fwms-final-pg-')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    run_program(pgbin/'initdb.exe', '-D', cluster/'data', '-U', OWNER,
                '--auth=trust', '--encoding=UTF8', '--no-locale', '--no-sync')
    # This new cluster contains synthetic data only; trust is confined to loopback.
    run_program(pgbin/'pg_ctl.exe', '-D', cluster/'data', '-l', cluster/'server.log',
                '-o', f'-h 127.0.0.1 -p {port} -F', '-w', 'start')
    connection = owner_connection('postgres')
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute('CREATE DATABASE fwms_demo_test')
            cursor.execute('CREATE ROLE fwms_demo_test_app LOGIN NOSUPERUSER NOCREATEDB '
                           'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS')
    finally:
        connection.close()
    with owner_sql() as cursor:
        cursor.execute((ROOT/'demo/schema.sql').read_text(encoding='utf-8'))
    for key in list(os.environ):
        if key.startswith(('FWMS_DEMO_', 'GOOGLE_')) or key in ('DATABASE_URL','SECRET_KEY','REDIS_URL'):
            os.environ.pop(key, None)
    os.environ.update(FWMS_DEMO_MODE='true',
                      FWMS_DEMO_DATABASE_URL=f'postgresql://{ROLE}@127.0.0.1:{port}/{DATABASE}',
                      FWMS_DEMO_SECRET_KEY=SYNTHETIC_SECRET,
                      FWMS_DEMO_FRONTEND_URL='http://localhost:5173')
    # Refuse secret-file reads by application imports and prohibit provider calls.
    for module in (builtins, io):
        original = module.open
        def guarded(file, *args, _original=original, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)) and Path(file).name.startswith('.env'):
                raise RuntimeError('Secret-file access forbidden')
            return _original(file, *args, **kwargs)
        module.open = guarded
    import requests
    import urllib.request
    def blocked(*args, **kwargs):
        raise RuntimeError('Provider requests forbidden')
    requests.sessions.Session.request = blocked
    urllib.request.urlopen = blocked
    from app.allocation import service as allocation
    from app.reports import snapshot_service as snapshots
    from app.admin import service as admin
    from app.db.pool import engine as actual_engine
    service, snapshot_service, admin_service, engine = allocation, snapshots, admin, actual_engine
    with engine.connect():
        pass  # The real restricted-role/marker checkout gate must pass.


class PostgreSQLAllocationTests(unittest.TestCase):
    def setUp(self):
        with owner_sql() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            tables = ','.join('public.'+row[0] for row in cursor.fetchall())
            cursor.execute('TRUNCATE '+tables+' RESTART IDENTITY CASCADE')
            cursor.execute((ROOT/'demo/fixtures.sql').read_text(encoding='utf-8'))
            cursor.execute("INSERT INTO cycle(academic_year_id,semester_id,status) "
                           "SELECT id,4,'OPEN' FROM academic_year")
            cursor.execute("INSERT INTO cycle(academic_year_id,semester_id,status) "
                           "SELECT id,6,'FROZEN' FROM academic_year")
            cursor.execute("UPDATE semester SET state='OPEN' WHERE id=4")
            cursor.execute("UPDATE semester SET state='FROZEN' WHERE id=6")
            cursor.execute("INSERT INTO program(name,ug_pg) VALUES ('Synthetic Programme B','UG')")
            cursor.execute("INSERT INTO subject(code,name,l,t,p,tch,credits) "
                           "VALUES ('SYN-B','Synthetic Programme B Course',3,1,0,4,4)")
            cursor.execute("""INSERT INTO subject_offering(subject_id,program_id,semester_id,section_id,
                shift,academic_year,academic_year_id)
                SELECT sub.id,1,sem.id,1,1,ay.name,ay.id
                FROM subject sub CROSS JOIN semester sem CROSS JOIN academic_year ay
                WHERE sub.code='SYN-CS101' AND sem.id IN (4,6)""")
            cursor.execute("""INSERT INTO subject_offering(subject_id,program_id,semester_id,section_id,
                shift,academic_year,academic_year_id)
                SELECT sub.id,2,2,1,1,ay.name,ay.id FROM subject sub CROSS JOIN academic_year ay
                WHERE sub.code='SYN-B'""")
            cursor.execute("""INSERT INTO faculty_preference(staff_id,subject_offering_id,preference_number,cycle_id)
                SELECT st.id,so.id,1,c.id FROM staff st JOIN subject_offering so ON so.semester_id=4
                JOIN cycle c ON c.semester_id=4 WHERE st.emp_code='SYN101'""")
            cursor.execute("""INSERT INTO faculty_preference(staff_id,subject_offering_id,preference_number,cycle_id)
                SELECT st.id,so.id,1,c.id FROM staff st JOIN subject_offering so ON so.program_id=2
                JOIN cycle c ON c.semester_id=2 WHERE st.emp_code='SYN102'""")
            cursor.execute("""INSERT INTO allocation(staff_id,subject_offering_id,l_assigned,t_assigned,p_assigned,cycle_id)
                SELECT st.id,so.id,3,1,0,c.id FROM staff st JOIN subject_offering so ON so.semester_id=6
                JOIN cycle c ON c.semester_id=6 WHERE st.emp_code='SYN101'""")

    def rows(self, table):
        with owner_sql() as cursor:
            cursor.execute('SELECT * FROM '+table+' ORDER BY id')
            return cursor.fetchall()

    def state(self):
        return {table:self.rows(table) for table in
                ('allocation','workload_summary','cycle','semester','audit_log','workload_snapshot')}

    def assert_totals(self):
        with owner_sql() as cursor:
            cursor.execute("""SELECT st.id, COALESCE(SUM(sub.tch),0)
                FROM staff st LEFT JOIN allocation a ON a.staff_id=st.id
                LEFT JOIN subject_offering so ON so.id=a.subject_offering_id
                LEFT JOIN subject sub ON sub.id=so.subject_id
                GROUP BY st.id ORDER BY st.id""")
            expected=dict(cursor.fetchall())
            cursor.execute("SELECT staff_id,tch_total FROM workload_summary WHERE semester_type='EVEN'")
            self.assertEqual(dict(cursor.fetchall()),expected)

    def wait_for_advisory_waiter(self):
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            with owner_sql() as cursor:
                cursor.execute("SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND NOT granted")
                if cursor.fetchone()[0]:
                    return
            time.sleep(.02)
        self.fail('Competing transaction did not wait on PostgreSQL advisory lock')

    def hold_first_allocation(self, other):
        entered,release=threading.Event(),threading.Event()
        real=service._allocate_in_transaction
        def allocate(session,scope,program_id=None):
            result=real(session,scope,program_id)
            if threading.current_thread().name.startswith('first'):
                entered.set()
                if not release.wait(4):
                    raise RuntimeError('Test synchronization expired')
            return result
        with patch.object(service,'_allocate_in_transaction',side_effect=allocate), \
             ThreadPoolExecutor(1,thread_name_prefix='first') as first, \
             ThreadPoolExecutor(1,thread_name_prefix='second') as second:
            a=first.submit(service.run_allocation,semester_id=2)
            try:
                self.assertTrue(entered.wait(3))
                b=second.submit(other)
                self.wait_for_advisory_waiter()
            finally:
                release.set()
            return a.result(timeout=8),b.result(timeout=8)

    def test_different_semesters_preserve_shared_and_frozen_contributions(self):
        frozen=self.rows('allocation')[-1]
        a,b=self.hold_first_allocation(lambda:service.run_allocation(semester_id=4))
        self.assertTrue(a['success'] and b['success'])
        self.assertIn(frozen,self.rows('allocation'))
        self.assert_totals()

    def test_same_semester_serializes_and_revalidates(self):
        a,b=self.hold_first_allocation(lambda:service.run_allocation(semester_id=2))
        self.assertTrue(a['success'])
        self.assertFalse(b['success'])
        self.assertEqual(len(self.rows('audit_log')),1)
        self.assert_totals()

    def test_programme_sequence_and_full_finalization(self):
        self.assertTrue(service.run_allocation(semester_id=2,program_id=1)['success'])
        self.assertTrue(service.run_allocation(semester_id=2,program_id=2)['success'])
        with self.assertRaises(RuntimeError):
            snapshot_service.create_snapshot(1)
        self.assertTrue(service.run_allocation(semester_id=2)['success'])
        self.assert_totals()
        self.assertTrue(service.run_allocation(semester_id=4,program_id=1)['success'])
        self.assertEqual({row[0]:row[3] for row in self.rows('cycle')},{1:'ALLOCATED',2:'ALLOCATED',3:'FROZEN'})

    def test_real_database_failure_rolls_back_whole_batch(self):
        before=self.state()
        with owner_sql() as cursor:
            cursor.execute("ALTER TABLE audit_log ADD CONSTRAINT fail_second "
                           "CHECK ((details->>'semester_id') IS DISTINCT FROM '4')")
        try:
            with self.assertRaises(Exception):
                service.run_all_open_semesters()
            self.assertEqual(self.state(),before)
        finally:
            with owner_sql() as cursor:
                cursor.execute('ALTER TABLE audit_log DROP CONSTRAINT fail_second')

    def test_hod_approval_waits_for_committed_allocation(self):
        a,b=self.hold_first_allocation(lambda:snapshot_service.create_snapshot(1))
        self.assertTrue(a['success'])
        self.assertEqual(b['semester_id'],2)
        with engine.connect() as connection:
            expected=snapshot_service._build_snapshot_data(connection,'2026-2027',2)
        with owner_sql() as cursor:
            cursor.execute('SELECT snapshot_data FROM workload_snapshot')
            self.assertEqual(cursor.fetchone()[0],expected)
        self.assertFalse(service.run_allocation(semester_id=2)['success'])

    def test_allocation_waits_for_approval_then_rejects_frozen_cycle(self):
        self.assertTrue(service.run_allocation(semester_id=2)['success'])
        entered,release=threading.Event(),threading.Event()
        real=snapshot_service._build_snapshot_data
        def build(*args):
            result=real(*args)
            entered.set()
            if not release.wait(4):
                raise RuntimeError('Test synchronization expired')
            return result
        with patch.object(snapshot_service,'_build_snapshot_data',side_effect=build), \
             ThreadPoolExecutor(2) as workers:
            approval=workers.submit(snapshot_service.create_snapshot,1)
            try:
                self.assertTrue(entered.wait(3))
                allocation=workers.submit(service.run_allocation,semester_id=2)
                self.wait_for_advisory_waiter()
            finally:
                release.set()
            self.assertEqual(approval.result(timeout=8)['semester_id'],2)
            self.assertFalse(allocation.result(timeout=8)['success'])

    def test_window_close_retains_frozen_semester(self):
        from app.coordinator.window_transactions import close_window_transaction
        frozen=next(row for row in self.rows('semester') if row[0]==6)
        with owner_sql() as cursor:
            cursor.execute("""INSERT INTO selection_window(name,start_time,end_time,
                max_subjects_per_staff,batch_id,specialization_id,status)
                VALUES ('Synthetic window',now()-interval '1 hour',now()+interval '1 hour',3,1,1,'OPEN')
                RETURNING id""")
            window_id=cursor.fetchone()[0]
        self.assertTrue(close_window_transaction(1,window_id)['success'])
        self.assertIn(frozen,self.rows('semester'))

    def test_native_launchers_health_probes_and_access_logging(self):
        # Exercise the serving commands against this cluster, from an empty cwd
        # so institutional Settings cannot discover the workspace's .env file.
        import yaml
        for demo in (False,True):
            with socket.socket() as listener:
                listener.bind(('127.0.0.1',0))
                http_port=listener.getsockname()[1]
            child_env={key:value for key,value in os.environ.items()
                       if key.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP')}
            child_env.update(PYTHONPATH=os.pathsep.join([str(ROOT),os.environ.get('PYTHONPATH','')]),
                             PYTHONDONTWRITEBYTECODE='1',PORT=str(http_port),ENV='production',
                             LOG_FILE=str(cluster/('demo.log' if demo else 'institutional.log')),
                             DEV_AUTH_BYPASS='false')
            if demo:
                child_env.update({key:value for key,value in os.environ.items() if key.startswith('FWMS_DEMO_')})
                command=[sys.executable,'-B',str(ROOT/'demo/start_backend.py')]
            else:
                child_env.update(DATABASE_URL=f'postgresql://{ROLE}@127.0.0.1:{port}/{DATABASE}',
                                 SECRET_KEY=SYNTHETIC_SECRET,GOOGLE_CLIENT_ID='synthetic-client',
                                 GOOGLE_CLIENT_SECRET='synthetic-oauth-secret',
                                 GOOGLE_REDIRECT_URI='http://127.0.0.1/unused-callback')
                command=[sys.executable,'-B','-m','app.start_backend']
            output_path=cluster/('demo-console.log' if demo else 'institutional-console.log')
            with output_path.open('wb') as output:
                process=subprocess.Popen(command,cwd=cluster,env=child_env,stdout=output,stderr=output,
                                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                try:
                    deadline=time.monotonic()+15
                    while True:
                        try:
                            client=http.client.HTTPConnection('127.0.0.1',http_port,timeout=1)
                            client.request('GET','/api/health?credential=synthetic-request-canary')
                            response=client.getresponse()
                            data=json.loads(response.read())
                            client.close()
                            break
                        except (OSError,http.client.HTTPException):
                            if process.poll() is not None or time.monotonic()>deadline:
                                self.fail('Native launcher failed to become healthy; inspect synthetic test logs')
                            time.sleep(.1)
                    self.assertEqual(response.status,200)
                    self.assertEqual(data.get('environment')=='synthetic-demo',demo)
                    client=http.client.HTTPConnection('127.0.0.1',http_port,timeout=3)
                    client.request('GET','/api/health/deep')
                    self.assertEqual(json.loads(client.getresponse().read())['database'],'ok')
                    client.close()
                    if demo:
                        probe=[sys.executable,'-B',str(ROOT/'demo/healthcheck.py')]
                    else:
                        compose=yaml.safe_load((ROOT/'docker-compose.prod.yml').read_text())
                        probe_code=shlex.split(compose['services']['app']['healthcheck']['test'][1])[2]
                        probe=[sys.executable,'-c',probe_code]
                    checked=subprocess.run(probe,cwd=cluster,env=child_env,stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL,timeout=5)
                    self.assertEqual(checked.returncode,0)
                finally:
                    process.terminate()
                    process.wait(timeout=8)
            logs=output_path.read_text(encoding='utf-8',errors='replace')
            logs+=Path(child_env['LOG_FILE']).read_text(encoding='utf-8',errors='replace')
            self.assertNotIn('synthetic-request-canary',logs)
            self.assertNotIn(SYNTHETIC_SECRET,logs)
            self.assertNotIn('postgresql://',logs)

    def test_lock_timeout_rolls_back_and_releases_connections(self):
        from app.db.workload import WORKLOAD_LOCK
        holder=owner_connection()
        before=self.state()
        try:
            with holder.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(%s,%s)',WORKLOAD_LOCK)
            with self.assertRaises(Exception) as error:
                service.run_allocation(semester_id=2)
            self.assertEqual(getattr(error.exception.orig,'pgcode',None),'55P03')
            self.assertEqual(self.state(),before)
        finally:
            holder.rollback();holder.close()
        self.assertTrue(service.run_allocation(semester_id=2)['success'])

    def test_override_keeps_other_semester_totals_and_summary_reader_works(self):
        self.assertTrue(service.run_all_open_semesters()['success'])
        with owner_sql() as cursor:
            cursor.execute("SELECT a.id FROM allocation a JOIN subject_offering so ON so.id=a.subject_offering_id "
                           "JOIN subject s ON s.id=so.subject_id WHERE so.semester_id=2 AND s.code='SYN-CS101'")
            allocation_id=cursor.fetchone()[0]
        self.assertTrue(admin_service.override_allocation(allocation_id,2,1)['success'])
        self.assert_totals()
        self.assertEqual(admin_service.get_workload_summary('2026-2027',2)['total_faculty'],2)


def main():
    global engine
    exit_code=1
    try:
        prepare_cluster()
        class RedactedResult(unittest.TextTestResult):
            def _exc_info_to_string(self,err,test):
                result=super()._exc_info_to_string(err,test)
                result=re.sub(r'postgres(?:ql)?://[^\s\'"<>]+','[REDACTED DATABASE URL]',result)
                return result.replace(SYNTHETIC_SECRET,'[REDACTED]')
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(PostgreSQLAllocationTests)
        result=unittest.TextTestRunner(verbosity=2,resultclass=RedactedResult).run(suite)
        exit_code=0 if result.wasSuccessful() else 1
    except Exception as error:
        print('Disposable PostgreSQL verification unavailable/failed ('+type(error).__name__+').',file=sys.stderr)
    finally:
        if engine is not None:
            engine.dispose()
        if cluster is not None:
            try:
                run_program(pgbin/'pg_ctl.exe','-D',cluster/'data','-m','immediate','-w','stop')
                # Never remove a cluster unless its own server has stopped.
                temporary_root=Path(tempfile.gettempdir()).resolve()
                assert cluster.resolve().parent==temporary_root and cluster.name.startswith('fwms-final-pg-')
                shutil.rmtree(cluster)
            except (RuntimeError,subprocess.TimeoutExpired,OSError):
                print('Disposable cluster retained; server stop requires inspection.',file=sys.stderr)
                exit_code=1
    return exit_code


if __name__=='__main__':
    sys.exit(main())
