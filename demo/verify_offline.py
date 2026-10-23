"""Offline demo regressions: real ASGI/JWT/SQL, SQLite only, external I/O blocked.

Run independently: python -B demo/verify_offline.py -v
PostgreSQL sequence/concurrency semantics are NOT verified by SQLite.
"""
import ast
import builtins
from contextlib import contextmanager
import io
import os
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _no_external_connection(sock, address):
    # Windows asyncio may use a loopback socket pair internally.
    if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
        raise AssertionError('External network is forbidden in offline tests')
    return _original_connect(sock, address)


_original_connect = socket.socket.connect
socket.socket.connect = _no_external_connection
socket.create_connection = Mock(side_effect=AssertionError('Network forbidden'))
socket.getaddrinfo = Mock(side_effect=AssertionError('DNS forbidden'))
_original_open, _original_io_open = builtins.open, io.open


def _guard_file(original):
    def guarded(file, *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)) and Path(file).name.startswith('.env'):
            raise AssertionError('Secret file access forbidden')
        return original(file, *args, **kwargs)
    return guarded


builtins.open = _guard_file(_original_open)
io.open = _guard_file(_original_io_open)
from app.demo.config import demo_settings_from_env
from app.demo.isolation import validate_demo_connection, DEMO_ISSUER

SYNTHETIC_ENV = {
    'FWMS_DEMO_MODE': 'true',
    'FWMS_DEMO_DATABASE_URL': 'postgresql://fwms_demo_test_app@localhost/fwms_demo_test',
    'FWMS_DEMO_SECRET_KEY': 'offline-synthetic-only-signing-key-0123456789',
    'FWMS_DEMO_FRONTEND_URL': 'http://localhost:5173',
}
with patch.dict(os.environ, SYNTHETIC_ENV, clear=True):
    from app.core.config import settings

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
import psycopg2
psycopg2.connect = Mock(side_effect=AssertionError('PostgreSQL forbidden in offline tests'))

_test_engine = None


@contextmanager
def _sqlite_transaction(*args, **kwargs):
    with Session(_test_engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


# Explicit adapters: no production pool or Google client is imported.
db_adapter = types.ModuleType('app.db.session')
db_adapter.get_transaction = _sqlite_transaction
sys.modules['app.db.session'] = db_adapter
google_adapter = types.ModuleType('app.auth.google_oauth')
google_adapter.oauth_client = Mock()
sys.modules['app.auth.google_oauth'] = google_adapter
from app.auth import router as auth
from app.auth import jwt_utils
from app.auth.dependencies import get_current_hod, get_current_coordinator, get_current_faculty
from app.admin import staff_router
from app.health import router as health

api = FastAPI()
api.include_router(auth.router)
api.include_router(staff_router.router)
api.include_router(health.router)


@api.get('/test/hod')
def hod_dashboard(user=Depends(get_current_hod)):
    return {'role': user.role}


@api.get('/test/coordinator')
def coordinator_dashboard(user=Depends(get_current_coordinator)):
    return {'role': user.role}


@api.get('/test/faculty')
def faculty_dashboard(user=Depends(get_current_faculty)):
    return {'role': user.role}


class ConfigurationTests(unittest.TestCase):
    def test_disabled_mode_does_not_read_demo_database(self):
        self.assertIsNone(demo_settings_from_env({'DATABASE_URL': 'not-used'}))

    def test_missing_configuration_fails_closed(self):
        for missing in ('FWMS_DEMO_DATABASE_URL','FWMS_DEMO_SECRET_KEY','FWMS_DEMO_FRONTEND_URL'):
            env = {k:v for k,v in SYNTHETIC_ENV.items() if k != missing}
            with self.subTest(variable=missing), self.assertRaises(RuntimeError):
                demo_settings_from_env(env)

    def test_normal_configuration_cannot_override_demo(self):
        env = dict(SYNTHETIC_ENV, DATABASE_URL='not-used', SECRET_KEY='not-used',
                   SESSION_BACKEND='redis', DEV_AUTH_BYPASS='true', GOOGLE_CLIENT_SECRET='not-used')
        result = demo_settings_from_env(env)
        self.assertEqual(result['DATABASE_URL'], SYNTHETIC_ENV['FWMS_DEMO_DATABASE_URL'])
        self.assertFalse(result['DEV_AUTH_BYPASS'])
        self.assertEqual(result['SESSION_BACKEND'], 'memory')
        self.assertEqual(result['GOOGLE_CLIENT_SECRET'], '')

    def test_wrong_database_or_role_rejected(self):
        for url in ('postgresql://fwms_demo_runtime@localhost/institution',
                    'postgresql://postgres@localhost/fwms_demo',
                    'postgresql://fwms_demo_runtime@localhost/fwms_demo?options=unsafe',
                    'postgresql://fwms_demo_runtime@localhost:bad/fwms_demo'):
            with self.subTest(), self.assertRaises(RuntimeError):
                demo_settings_from_env(dict(SYNTHETIC_ENV, FWMS_DEMO_DATABASE_URL=url))

    def test_exact_hosted_and_local_database_role_pairs(self):
        for database, role in (('fwms_demo', 'fwms_demo_runtime'),
                               ('fwms_demo_test', 'fwms_demo_test_app')):
            env = dict(SYNTHETIC_ENV, FWMS_DEMO_DATABASE_URL=f'postgresql://{role}@localhost/{database}')
            self.assertTrue(demo_settings_from_env(env)['DEMO_MODE'])

    def test_old_role_and_swapped_database_role_pairs_rejected(self):
        for database, role in (('fwms_demo', 'fwms_demo_app'),
                               ('fwms_demo_test', 'fwms_demo_app'),
                               ('fwms_demo', 'fwms_demo_test_app'),
                               ('fwms_demo_test', 'fwms_demo_runtime')):
            env = dict(SYNTHETIC_ENV, FWMS_DEMO_DATABASE_URL=f'postgresql://{role}@localhost/{database}')
            with self.subTest(database=database, role=role), self.assertRaises(RuntimeError):
                demo_settings_from_env(env)

    def test_invalid_mode_secret_and_origin_rejected(self):
        for key, value in (('FWMS_DEMO_MODE','yes'),('FWMS_DEMO_SECRET_KEY','short'),
                           ('FWMS_DEMO_FRONTEND_URL','http://public.example.com')):
            with self.subTest(variable=key), self.assertRaises(RuntimeError):
                demo_settings_from_env(dict(SYNTHETIC_ENV, **{key:value}))

    def test_demo_settings_loaded_without_dotenv(self):
        self.assertTrue(settings.DEMO_MODE)
        self.assertFalse(settings.DEV_AUTH_BYPASS)
        self.assertEqual(settings.FRONTEND_URL, 'http://localhost:5173')


class IsolationTests(unittest.TestCase):
    def connection(self, identity=None, marker=('synthetic-only',1), permissions=(False,False,False)):
        connection = Mock()
        connection.cursor.return_value.fetchone.side_effect = [
            identity if identity is not None else ('fwms_demo_test','fwms_demo_test_app') + (False,) * 8,
            marker, permissions,
        ]
        return connection

    def test_verified_connection_allowed(self):
        connection = self.connection()
        validate_demo_connection(connection)
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.cursor.return_value.close.assert_called_once()

    def test_hosted_restricted_runtime_connection_allowed(self):
        connection = self.connection(identity=('fwms_demo', 'fwms_demo_runtime') + (False,) * 8)
        validate_demo_connection(connection)
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()

    def test_old_role_and_wrong_database_role_pairs_refused_before_marker(self):
        for database, role in (('fwms_demo', 'fwms_demo_app'),
                               ('fwms_demo_test', 'fwms_demo_app'),
                               ('fwms_demo', 'fwms_demo_test_app'),
                               ('fwms_demo_test', 'fwms_demo_runtime')):
            connection = self.connection(identity=(database, role) + (False,) * 8)
            with self.subTest(database=database, role=role), self.assertRaises(RuntimeError):
                validate_demo_connection(connection)
            self.assertEqual(connection.cursor.return_value.execute.call_count, 1)
            connection.rollback.assert_called_once()

    def test_institutional_database_refused_before_marker_or_data(self):
        connection = self.connection(identity=('institution','fwms_demo_runtime') + (False,) * 8)
        with self.assertRaises(RuntimeError):
            validate_demo_connection(connection)
        self.assertEqual(connection.cursor.return_value.execute.call_count,1)
        connection.rollback.assert_called_once()

    def test_privileged_or_inheriting_role_refused(self):
        for database, role in (('fwms_demo', 'fwms_demo_runtime'),
                               ('fwms_demo_test', 'fwms_demo_test_app')):
            for index in range(2, 10):
                row = [database, role] + [False] * 8
                row[index] = True
                connection = self.connection(identity=tuple(row))
                with self.subTest(database=database, flag=index), self.assertRaises(RuntimeError):
                    validate_demo_connection(connection)
                self.assertEqual(connection.cursor.return_value.execute.call_count, 1)
                connection.rollback.assert_called_once()

    def test_unknown_or_incomplete_catalog_flags_fail_closed(self):
        rows = [(), ('fwms_demo', 'fwms_demo_runtime') + (False,) * 7,
                ('fwms_demo', 'fwms_demo_runtime') + (False,) * 7 + (None,)]
        for row in rows:
            with self.subTest(), self.assertRaises(RuntimeError):
                validate_demo_connection(self.connection(identity=row))

    def test_runtime_object_owner_refused_before_marker_or_application_queries(self):
        connection = self.connection(identity=('fwms_demo', 'fwms_demo_runtime') + (False,) * 7 + (True,))
        with self.assertRaises(RuntimeError):
            validate_demo_connection(connection)
        self.assertEqual(connection.cursor.return_value.execute.call_count, 1)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.cursor.return_value.close.assert_called_once()

    def test_catalog_query_checks_ownership_without_confusing_acl_grants(self):
        connection = self.connection(identity=('fwms_demo', 'fwms_demo_runtime') + (False,) * 8)
        validate_demo_connection(connection)
        query = connection.cursor.return_value.execute.call_args_list[0].args[0]
        self.assertIn('pg_catalog.pg_shdepend', query)
        self.assertIn("refclassid = 'pg_catalog.pg_authid'::regclass", query)
        self.assertIn("refobjid = r.oid AND deptype = 'o'", query)
        self.assertIn('WHERE member = r.oid', query)

    def test_marker_missing_or_mutable_refused(self):
        for connection in (self.connection(marker=None), self.connection(marker=('wrong',1)),
                           self.connection(permissions=(True,False,False)),
                           self.connection(permissions=(False,True,False)),
                           self.connection(permissions=(False,False,True)),
                           self.connection(permissions=(False,False,None)),
                           self.connection(permissions=())):
            with self.subTest(), self.assertRaises(RuntimeError):
                validate_demo_connection(connection)

    def test_database_error_is_sanitized(self):
        connection = self.connection()
        connection.cursor.return_value.execute.side_effect = RuntimeError('SENSITIVE_TEST_ERROR')
        with self.assertRaisesRegex(RuntimeError,'^Demo database isolation verification failed$'):
            validate_demo_connection(connection)

    def test_real_pool_checkout_listener_refuses_institutional_database(self):
        from app.db.pool import _verify_demo_checkout
        connection = self.connection(identity=('institution','fwms_demo_runtime') + (False,) * 8)
        with self.assertRaises(RuntimeError):
            _verify_demo_checkout(connection,None,None)
        self.assertEqual(connection.cursor.return_value.execute.call_count,1)


class DemoApiTests(unittest.TestCase):
    def setUp(self):
        global _test_engine
        settings.DEMO_MODE = True
        _test_engine = create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        with _test_engine.begin() as connection:
            connection.exec_driver_sql('''CREATE TABLE staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                role TEXT NOT NULL, emp_code TEXT UNIQUE, is_active BOOLEAN DEFAULT 1,
                is_coordinator BOOLEAN DEFAULT 0, designation TEXT, shift TEXT, tch_norm INTEGER,
                total_workload_norm INTEGER, is_class_teacher BOOLEAN DEFAULT 0,
                ct_program TEXT, ct_section TEXT, ct_semester TEXT, ct_shift INTEGER, ct_curriculum_year TEXT)''')
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        _test_engine.dispose()
        settings.DEMO_MODE = True

    def login(self,role='hod'):
        response = self.client.post('/api/auth/demo-login',params={'role':role})
        self.assertEqual(response.status_code,200)
        data = response.json()
        self.assertEqual(data['token_type'],'bearer')
        self.assertEqual(data['user']['role'],role)
        return {'Authorization':'Bearer ' + data['access_token']}

    def count(self):
        with _test_engine.connect() as connection:
            return connection.execute(text('SELECT count(*) FROM staff')).scalar()

    def test_creation_reuse_and_unique_primary_keys(self):
        ids = []
        for role in ('hod','tt_coordinator','faculty'):
            first = self.client.get('/api/auth/me',headers=self.login(role))
            second = self.client.get('/api/auth/me',headers=self.login(role))
            self.assertEqual(first.status_code,200)
            self.assertEqual(second.status_code,200)
            self.assertEqual(first.json()['staff_id'],second.json()['staff_id'])
            self.assertTrue(first.json()['is_demo'])
            ids.append(first.json()['staff_id'])
        self.assertEqual(len(set(ids)),3)
        self.assertEqual(self.count(),3)

    def test_role_guards_and_staff_visibility(self):
        allowed = {'hod':(200,200,403,200),'tt_coordinator':(403,200,403,403),'faculty':(403,403,200,403)}
        paths = ('/test/hod','/test/coordinator','/test/faculty','/api/admin/staff')
        for role,statuses in allowed.items():
            headers = self.login(role)
            for path,status in zip(paths,statuses):
                with self.subTest(role=role,path=path):
                    self.assertEqual(self.client.get(path,headers=headers).status_code,status)

    def test_unauthenticated_access_blocked(self):
        for path in ('/api/auth/me','/api/admin/staff','/test/hod','/test/coordinator','/test/faculty'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code,401)

    def test_health_marker_is_demo_only(self):
        self.assertEqual(self.client.get('/api/health').json().get('environment'),'synthetic-demo')
        settings.DEMO_MODE = False
        self.assertNotIn('environment',self.client.get('/api/health').json())

    def test_demo_deep_health_does_not_disclose_database_error(self):
        with patch.object(health,'get_transaction',side_effect=RuntimeError('SENSITIVE_TEST_ERROR')):
            response = self.client.get('/api/health/deep')
        self.assertEqual(response.json()['database_error'],'Demo database unavailable')
        self.assertNotIn('SENSITIVE_TEST_ERROR',response.text)

    def test_normal_backend_refuses_public_demo_without_database_access(self):
        settings.DEMO_MODE = False
        with patch.object(auth,'get_transaction',side_effect=AssertionError('Must not query')):
            self.assertEqual(self.client.post('/api/auth/demo-login').status_code,403)
        self.assertEqual(self.count(),0)

    def test_invalid_role_cannot_select_an_arbitrary_account(self):
        self.assertEqual(self.client.post('/api/auth/demo-login?role=admin').status_code,422)
        self.assertEqual(self.count(),0)

    def test_conflicting_employee_code_is_not_deleted_or_overwritten(self):
        with _test_engine.begin() as connection:
            connection.execute(text("INSERT INTO staff(email,name,role,emp_code) VALUES ('other@demo.example.com','Synthetic','faculty','DEMO001')"))
        self.assertEqual(self.client.post('/api/auth/demo-login').status_code,503)
        self.assertEqual(self.count(),1)

    def test_existing_identity_role_or_active_mismatch_fails_closed(self):
        self.login()
        with _test_engine.begin() as connection:
            connection.execute(text("UPDATE staff SET role='faculty',is_active=false WHERE emp_code='DEMO001'"))
        self.assertEqual(self.client.post('/api/auth/demo-login').status_code,503)
        self.assertEqual(self.count(),1)

    def test_primary_key_collision_produces_safe_503_no_repair(self):
        with _test_engine.begin() as connection:
            connection.execute(text("INSERT INTO staff(email,name,role,emp_code) VALUES ('other@demo.example.com','Synthetic','faculty','SYN101')"))
            # Deliberately broken ID-producing trigger in SQLite ONLY.
            # Real SQL uniqueness failure, not a PostgreSQL sequence-drift claim.
            connection.exec_driver_sql('''CREATE TRIGGER force_id_collision AFTER INSERT ON staff
                BEGIN UPDATE staff SET id=1 WHERE id=NEW.id; END''')
        response = self.client.post('/api/auth/demo-login')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('UNIQUE constraint',response.text)
        self.assertEqual(self.count(),1)

    def test_signing_failure_rolls_back_new_account(self):
        with patch.object(auth,'create_jwt',side_effect=RuntimeError('SENSITIVE_TEST_ERROR')):
            self.assertEqual(self.client.post('/api/auth/demo-login').status_code,503)
        self.assertEqual(self.count(),0)

    def test_demo_tokens_rejected_by_normal_backend_even_with_same_signing_key(self):
        headers = self.login()
        settings.DEMO_MODE = False
        self.assertEqual(self.client.get('/api/admin/staff',headers=headers).status_code,401)

    def test_normal_tokens_rejected_by_demo_backend(self):
        self.login()
        settings.DEMO_MODE = False
        token = jwt_utils.create_jwt(1,'demo@fwms-demo.com','Synthetic','hod')
        settings.DEMO_MODE = True
        self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code,401)

    def test_role_is_read_from_database_not_token(self):
        headers = self.login()
        with _test_engine.begin() as connection:
            connection.execute(text("UPDATE staff SET role='faculty' WHERE emp_code='DEMO001'"))
        self.assertEqual(self.client.get('/api/admin/staff',headers=headers).status_code,403)

    def test_google_routes_disabled_in_demo_without_calling_provider(self):
        google_adapter.oauth_client.reset_mock()
        self.assertEqual(self.client.get('/api/auth/login').status_code,403)
        self.assertEqual(self.client.get('/api/auth/callback?code=synthetic').status_code,403)
        self.assertEqual(len(google_adapter.oauth_client.mock_calls),0)

    def test_normal_google_flow_contract_with_mocked_provider(self):
        self.login()
        settings.DEMO_MODE = False
        google_adapter.oauth_client.get_authorization_url.return_value = 'https://accounts.example.com/authorize'
        google_adapter.oauth_client.exchange_code_for_token.return_value = {'email':'demo@fwms-demo.com'}
        self.assertEqual(self.client.get('/api/auth/login').status_code,200)
        response = self.client.get('/api/auth/callback?code=synthetic',follow_redirects=False)
        self.assertEqual(response.status_code,302)
        self.assertIn('/dashboard?token=',response.headers['location'])
        self.assertIn(settings.SESSION_COOKIE_NAME,response.headers['set-cookie'])

    def test_existing_demo_and_auth_pytest_suites_with_isolated_database_adapter(self):
        # Existing files import actual app.main. Only DB/provider dependencies are
        # adapted above; production config, PostgreSQL and external I/O are blocked.
        # No startup lifespan is entered by their existing TestClient usage.
        import pytest
        filenames = ['test_demo_login.py','test_auth.py']
        expected = sum(sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in
                           ast.parse((ROOT/'tests'/f).read_text(encoding='utf-8')).body) for f in filenames)
        class Results:
            passed = 0
            def pytest_runtest_logreport(self,report):
                if report.when == 'call' and report.passed:
                    self.passed += 1
        results = Results()
        with patch.dict(os.environ,dict(SYNTHETIC_ENV,DATABASE_URL='isolated-sqlite-test-only',
                                       PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'),clear=True):
            code = pytest.main(['-q','-c',os.devnull,'-p','no:cacheprovider'] +
                               [str(ROOT/'tests'/f) for f in filenames],plugins=[results])
        self.assertEqual(code,0)
        self.assertEqual(results.passed,expected)

    def test_full_demo_app_excludes_debug_routes(self):
        from app.main import create_app
        app = create_app()
        self.assertFalse(any(route.path.startswith('/api/debug') for route in app.routes))

    def test_full_demo_app_unmounts_all_maintenance_aliases_and_docs(self):
        """Actual requests must not reach historical diagnostics or repairs."""
        from app.main import create_app
        from app.reports.router import maintenance_router

        explicitly_removed = {
            '/api/reports/export/staff-debug',
            '/api/reports/debug-offerings',
            '/api/reports/admin/db-state',
            '/api/reports/admin/fix-duplicate-programs',
            '/api/reports/admin/seed-mca-odd',
            '/api/reports/admin/fix-shift2-offerings',
            '/api/reports/admin/fix-shift-from-program',
            '/api/reports/admin/create-shift2-offerings',
            '/api/reports/admin/create-secb-offerings',
        }
        maintenance_paths = {route.path for route in maintenance_router.routes}
        self.assertTrue(explicitly_removed <= maintenance_paths)

        app = create_app()
        self.assertIsNone(app.docs_url)
        self.assertIsNone(app.redoc_url)
        self.assertIsNone(app.openapi_url)
        self.assertFalse(maintenance_paths & {route.path for route in app.routes})

        client = TestClient(app)
        try:
            # Handlers obtain a transaction at call time.  A 404 therefore
            # proves every path below is rejected before any mutation can run.
            with patch('app.db.session.get_transaction',
                       side_effect=AssertionError('Unserved route opened a transaction')):
                for route in maintenance_router.routes:
                    path = route.path
                    for parameter in route.param_convertors:
                        path = path.replace('{' + parameter + '}', 'SYNTHETIC')
                    method = sorted(route.methods - {'HEAD', 'OPTIONS'})[0]
                    response = client.request(method, path)
                    self.assertEqual(response.status_code, 404, (method, path))
                for path in ('/docs', '/redoc', '/openapi.json'):
                    self.assertEqual(client.get(path).status_code, 404, path)
        finally:
            client.close()

    def test_institutional_app_retains_documentation_routes(self):
        from app.main import create_app
        original_demo_mode = settings.DEMO_MODE
        settings.DEMO_MODE = False
        try:
            app = create_app()
            self.assertEqual(app.docs_url, '/docs')
            self.assertEqual(app.redoc_url, '/redoc')
            self.assertEqual(app.openapi_url, '/openapi.json')
            client = TestClient(app)
            try:
                self.assertEqual(client.get('/docs').status_code, 200)
                self.assertEqual(client.get('/openapi.json').status_code, 200)
            finally:
                client.close()
        finally:
            settings.DEMO_MODE = original_demo_mode

    def test_full_demo_startup_fails_before_logging_or_application_queries(self):
        from app.main import app
        with patch('app.db.pool.engine.connect',side_effect=RuntimeError('Demo isolation unavailable')):
            with self.assertRaisesRegex(RuntimeError,'Demo isolation unavailable'):
                with TestClient(app):
                    pass


if __name__ == '__main__':
    unittest.main()
