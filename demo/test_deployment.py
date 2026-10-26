"""Dedicated launcher/probe regressions. No DB/provider/network or secret files."""
import contextlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

import psycopg2
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'demo' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launcher = load('demo_launcher_test', 'start_backend.py')
probe = load('demo_probe_test', 'healthcheck.py')
from app.demo import startup as demo_startup


def configuration():
    return {'FWMS_DEMO_MODE': 'true', 'FWMS_DEMO_DATABASE_URL': 'postgresql://fwms_demo_runtime@localhost/fwms_demo',
            'FWMS_DEMO_SECRET_KEY': 'x' * 40, 'FWMS_DEMO_FRONTEND_URL': 'https://synthetic.example.com', 'PORT': '8001'}


class DeploymentTests(unittest.TestCase):
    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _Engine:
        def __init__(self, outcomes):
            self.outcomes = list(outcomes)
            self.calls = 0

        def connect(self):
            self.calls += 1
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

    @staticmethod
    def _transport_error(message='SSL connection has been closed unexpectedly'):
        return OperationalError(
            'show standard_conforming_strings',
            {},
            psycopg2.OperationalError(message),
        )

    def test_startup_retries_transient_connection_then_runs_verified_checkout(self):
        engine = self._Engine([self._transport_error(), self._Connection()])
        sleep = Mock()
        demo_startup.verify_demo_startup_database(engine, sleep=sleep)
        self.assertEqual(engine.calls, 2)
        sleep.assert_called_once_with(0.5)

    def test_startup_stops_after_bounded_transient_connection_retries(self):
        engine = self._Engine([self._transport_error()] * 3)
        sleep = Mock()
        with self.assertRaises(OperationalError):
            demo_startup.verify_demo_startup_database(engine, sleep=sleep)
        self.assertEqual(engine.calls, 3)
        self.assertEqual(sleep.call_args_list, [((0.5,),), ((1.0,),)])

    def test_startup_does_not_retry_isolation_or_configuration_failures(self):
        for failure in (
            RuntimeError('Demo database isolation verification failed'),
            self._transport_error('password authentication failed for user'),
        ):
            with self.subTest(failure=type(failure).__name__):
                engine = self._Engine([failure])
                sleep = Mock()
                with self.assertRaises(type(failure)):
                    demo_startup.verify_demo_startup_database(engine, sleep=sleep)
                self.assertEqual(engine.calls, 1)
                sleep.assert_not_called()

    def test_launcher_refuses_absent_false_and_invalid_demo_mode(self):
        for mode in (None, 'false', 'yes'):
            env = configuration()
            if mode is None:
                del env['FWMS_DEMO_MODE']
            else:
                env['FWMS_DEMO_MODE'] = mode
            with self.assertRaises(RuntimeError):
                launcher.validate_startup(env)

    def test_missing_demo_variables_do_not_fall_back_to_ordinary_configuration(self):
        for name in ('FWMS_DEMO_DATABASE_URL', 'FWMS_DEMO_SECRET_KEY', 'FWMS_DEMO_FRONTEND_URL'):
            env = configuration()
            del env[name]
            env.update(DATABASE_URL='must-not-be-consumed', SECRET_KEY='must-not-be-consumed')
            with self.assertRaises(RuntimeError):
                launcher.validate_startup(env)

    def test_invalid_database_name_role_and_port_fail_closed(self):
        for name, value in [('FWMS_DEMO_DATABASE_URL', 'postgresql://fwms_demo_runtime@localhost/institution'),
                            ('FWMS_DEMO_DATABASE_URL', 'postgresql://postgres@localhost/fwms_demo'),
                            ('PORT', 'invalid'), ('PORT', '0'), ('PORT', '65536')]:
            with self.assertRaises(RuntimeError):
                launcher.validate_startup(dict(configuration(), **{name: value}))

    def test_launcher_accepts_only_exact_hosted_and_local_role_pairs(self):
        for database, role in (('fwms_demo', 'fwms_demo_runtime'),
                               ('fwms_demo_test', 'fwms_demo_test_app')):
            env = dict(configuration(), FWMS_DEMO_DATABASE_URL=f'postgresql://{role}@localhost/{database}')
            result, port = launcher.validate_startup(env)
            self.assertTrue(result['DEMO_MODE'])
            self.assertEqual(port, 8001)
        for database, role in (('fwms_demo', 'fwms_demo_app'),
                               ('fwms_demo', 'fwms_demo_test_app'),
                               ('fwms_demo_test', 'fwms_demo_runtime')):
            env = dict(configuration(), FWMS_DEMO_DATABASE_URL=f'postgresql://{role}@localhost/{database}')
            with self.subTest(database=database, role=role), self.assertRaises(RuntimeError):
                launcher.validate_startup(env)

    def test_schema_grants_only_to_exact_hosted_and_local_roles(self):
        schema = (ROOT / 'demo/schema.sql').read_text(encoding='utf-8')
        self.assertIn("WHEN 'fwms_demo' THEN 'fwms_demo_runtime' ELSE 'fwms_demo_test_app' END", schema)
        self.assertNotIn('fwms_demo_app', schema)
        self.assertIn('Refusing non-empty database', schema)
        self.assertIn('REVOKE ALL ON SCHEMA public FROM PUBLIC', schema)
        self.assertIn('GRANT SELECT ON fwms_demo_meta.environment', schema)
        self.assertNotIn('GRANT ALL', schema)

    def test_failed_validation_does_not_import_application_or_echo_configuration(self):
        env = configuration()
        del env['FWMS_DEMO_FRONTEND_URL']
        output = io.StringIO()
        import builtins
        original_import = builtins.__import__
        imports = []

        def guarded(name, *args, **kwargs):
            if name in ('uvicorn', 'app.main') or (name == 'app' and 'main' in (kwargs.get('fromlist') or (args[2] if len(args) > 2 else ()))):
                imports.append(name)
                raise AssertionError('Application import before validation')
            return original_import(name, *args, **kwargs)

        with patch.dict(os.environ, env, clear=True), patch('builtins.__import__', guarded), contextlib.redirect_stderr(output):
            self.assertEqual(launcher.main(), 1)
        self.assertTrue('postgresql://' not in output.getvalue(), 'Database URL appeared in diagnostic')
        self.assertTrue(env['FWMS_DEMO_SECRET_KEY'] not in output.getvalue(), 'Secret appeared in diagnostic')
        self.assertFalse(imports, 'Application import occurred before validation')

    def test_valid_launcher_runs_only_asgi_app_without_shell_or_migrations(self):
        application = types.ModuleType('app.main')
        application.app = object()
        application.configure_logging = Mock()
        uvicorn = types.ModuleType('uvicorn')
        uvicorn.run = Mock()
        import app
        env = dict(configuration(), DATABASE_URL='must-not-be-consumed', SECRET_KEY='must-not-be-consumed')
        with patch.dict(os.environ, env, clear=True), patch.dict(sys.modules, {'app.main': application, 'uvicorn': uvicorn}), \
                patch.object(app, 'main', application, create=True), \
                patch('os.system', side_effect=AssertionError('Shell forbidden')):
            self.assertEqual(launcher.main(), 0)
            self.assertNotIn('DATABASE_URL', os.environ)
            self.assertNotIn('SECRET_KEY', os.environ)
        args, kwargs = uvicorn.run.call_args
        self.assertIs(args[0], application.app)
        self.assertEqual(kwargs['host'], '0.0.0.0')
        self.assertEqual(kwargs['port'], 8001)
        self.assertFalse(kwargs['access_log'])

    def test_log_redaction_covers_messages_json_extras_and_tracebacks(self):
        secrets = ('postgresql://synthetic:private@localhost/fwms_demo', 'x' * 40 + '\\"')

        class JSONExtras(logging.Formatter):
            def format(self, record):
                return json.dumps({'message': record.getMessage(), 'extra': record.extra,
                                   'exception': self.formatException(record.exc_info)})

        try:
            raise RuntimeError(secrets[0])
        except RuntimeError:
            record = logging.LogRecord('demo', logging.ERROR, __file__, 1, '%s', (secrets[1],), sys.exc_info())
        record.extra = secrets[1]
        result = launcher.RedactingFormatter(JSONExtras(), secrets).format(record)
        for value in secrets:
            self.assertTrue(value not in result and json.dumps(value)[1:-1] not in result, 'Configured secret leaked')
        self.assertTrue('[REDACTED' in result)

    def test_arbitrary_database_urls_and_bearer_tokens_are_redacted(self):
        result = launcher.redact('postgresql://synthetic:private@localhost/other Bearer opaque-value eyJabc.def.ghi', ())
        self.assertTrue('synthetic:private' not in result and 'opaque-value' not in result and 'eyJabc' not in result)

    def test_formatter_failure_does_not_dump_raw_record(self):
        formatter = Mock()
        formatter.format.side_effect = RuntimeError('Unsafe formatter input')
        record = logging.LogRecord('demo', logging.ERROR, __file__, 1, 'Do not echo', (), None)
        self.assertEqual(launcher.RedactingFormatter(formatter, ()).format(record), 'Demo log event suppressed (formatting error)')

    def test_health_probe_is_loopback_only_and_requires_demo_marker(self):
        class Response(io.BytesIO):
            status = 200

        for body, expected in [({'status': 'ok', 'environment': 'synthetic-demo'}, True), ({'status': 'ok'}, False),
                               ({'status': 'error', 'environment': 'synthetic-demo'}, False)]:
            opener = Mock()
            opener.open.return_value = Response(json.dumps(body).encode())
            self.assertEqual(probe.check_health({'PORT': '8001'}, opener), expected)
            opener.open.assert_called_once_with('http://127.0.0.1:8001/api/health', timeout=3)
        self.assertIsNone(probe.NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_actual_health_route_returns_expected_demo_contract_without_database_access(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        config = types.ModuleType('app.core.config')
        config.settings = types.SimpleNamespace(DEMO_MODE=True)
        database = types.ModuleType('app.db.session')
        database.get_transaction = Mock(side_effect=AssertionError('Database access forbidden'))
        with patch.dict(sys.modules, {'app.core.config': config, 'app.db.session': database}):
            spec = importlib.util.spec_from_file_location('isolated_health_contract', ROOT / 'app/health/router.py')
            health = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(health)
            api = FastAPI()
            api.include_router(health.router)
            with TestClient(api) as client:
                response = client.get('/api/health')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {'status': 'ok', 'service': 'fwms-api', 'environment': 'synthetic-demo'})
        database.get_transaction.assert_not_called()


if __name__ == '__main__':
    class SafeResult(unittest.TextTestResult):
        def _exc_info_to_string(self, err, test):
            return err[0].__name__ + ': isolated deployment assertion failed; no configuration values emitted\n'
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=SafeResult, verbosity=2))
