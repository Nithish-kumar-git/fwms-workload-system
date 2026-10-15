"""Opt-in integration checks for an ALREADY PREPARED local synthetic test DB.

This creates/reuses synthetic demo accounts. It never applies schema/fixtures,
repairs sequences, deletes records, or connects to a remote database.
"""
import builtins
import io
import os
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def prepare():
    if os.environ.get('FWMS_DEMO_PG_TEST') != 'true':
        raise RuntimeError('Set FWMS_DEMO_PG_TEST=true only after preparing the local synthetic test database')
    from app.demo.config import demo_settings_from_env
    configuration = demo_settings_from_env(os.environ)
    if not configuration:
        raise RuntimeError('FWMS_DEMO_MODE=true is required')
    database = urlsplit(configuration['DATABASE_URL'])
    if (database.hostname not in ('localhost','127.0.0.1','::1') or database.path != '/fwms_demo_test'
            or database.username != 'fwms_demo_test_app'):
        raise RuntimeError('Integration checks require the dedicated LOCAL fwms_demo_test database')
    for module in (builtins,io):
        original = module.open
        def guarded(file,*args,_original=original,**kwargs):
            if isinstance(file,(str,bytes,os.PathLike)) and Path(file).name.startswith('.env'):
                raise RuntimeError('Secret-file access forbidden')
            return _original(file,*args,**kwargs)
        module.open = guarded
    # Prevent HTTP/provider calls. TestClient uses in-process ASGI transport.
    import urllib.request
    import requests
    def blocked(*args,**kwargs):
        raise RuntimeError('External provider requests forbidden during DB integration checks')
    urllib.request.urlopen = blocked
    requests.sessions.Session.request = blocked


class PostgreSQLDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prepare()
        from fastapi import Depends,FastAPI
        from fastapi.testclient import TestClient
        from app.auth import router as auth
        from app.admin import staff_router
        from app.auth.dependencies import get_current_coordinator,get_current_faculty
        from app.db.pool import engine
        # Actual checkout guard must pass before even a read-only assertion.
        with engine.connect():
            pass
        cls.engine = engine
        cls.app = FastAPI()
        cls.app.include_router(auth.router)
        cls.app.include_router(staff_router.router)
        @cls.app.get('/test/coordinator')
        def coordinator(user=Depends(get_current_coordinator)):
            return {'role':user.role}
        @cls.app.get('/test/faculty')
        def faculty(user=Depends(get_current_faculty)):
            return {'role':user.role}
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.engine.dispose()

    def test_create_repeated_login_unique_ids_and_role_access(self):
        identities = []
        for role in ('hod','tt_coordinator','faculty'):
            response = self.client.post('/api/auth/demo-login',params={'role':role})
            self.assertEqual(response.status_code,200)
            headers = {'Authorization':'Bearer '+response.json()['access_token']}
            info = self.client.get('/api/auth/me',headers=headers)
            self.assertEqual(info.status_code,200)
            identities.append(info.json()['staff_id'])
            again = self.client.post('/api/auth/demo-login',params={'role':role})
            self.assertEqual(again.status_code,200)
            from app.auth.jwt_utils import verify_jwt
            self.assertTrue(verify_jwt(again.json()['access_token'])['sub'] == str(identities[-1]))
            for path,expected in (('/api/admin/staff',200 if role=='hod' else 403),
                                  ('/test/coordinator',200 if role!='faculty' else 403),
                                  ('/test/faculty',200 if role=='faculty' else 403)):
                self.assertEqual(self.client.get(path,headers=headers).status_code,expected)
        self.assertEqual(len(set(identities)),3)

    def test_concurrent_repeated_login(self):
        from concurrent.futures import ThreadPoolExecutor
        from fastapi.testclient import TestClient
        from app.auth.jwt_utils import verify_jwt
        def login(_):
            with TestClient(self.app) as client:
                response = client.post('/api/auth/demo-login')
                if response.status_code != 200:
                    raise RuntimeError('Concurrent synthetic login failed')
                return verify_jwt(response.json()['access_token'])['sub']
        with ThreadPoolExecutor(max_workers=4) as pool:
            identities = list(pool.map(login,range(4)))
        self.assertEqual(len(set(identities)),1)

    def test_no_institutional_email_or_duplicate_primary_keys(self):
        from sqlalchemy import text
        with self.engine.connect() as connection:
            unexpected = connection.execute(text("""SELECT count(*) FROM staff
                WHERE email <> 'demo@fwms-demo.com' AND email NOT LIKE '%@demo.example.com'""")).scalar()
            counts = connection.execute(text('SELECT count(*),count(DISTINCT id) FROM staff')).fetchone()
        self.assertEqual(unexpected,0)
        self.assertEqual(counts[0],counts[1])

    def test_unauthenticated_staff_access_denied(self):
        self.assertEqual(self.client.get('/api/admin/staff').status_code,401)


if __name__ == '__main__':
    # Report only test outcomes and exception classes, never connection error text.
    class SanitizedResult(unittest.TextTestResult):
        def _exc_info_to_string(self,err,test):
            return err[0].__name__ + ': local demo integration check failed (details withheld)\n'
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=SanitizedResult,verbosity=2))
