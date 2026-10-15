"""Verify every checked-out DB connection before any application query."""

DEMO_ISSUER = "fwms-synthetic-demo"
DEMO_ROLES = {"fwms_demo": "fwms_demo_runtime", "fwms_demo_test": "fwms_demo_test_app"}


def validate_demo_connection(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT current_database(), current_user, rolsuper, rolcreatedb,
                   rolcreaterole, rolbypassrls, rolreplication, rolinherit,
                   EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members WHERE member = r.oid),
                   EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend
                           WHERE refclassid = 'pg_catalog.pg_authid'::regclass
                             AND refobjid = r.oid AND deptype = 'o')
            FROM pg_catalog.pg_roles r WHERE rolname = current_user
        """)
        row = cursor.fetchone()
        if (not row or len(row) != 10 or DEMO_ROLES.get(row[0]) != row[1]
                or any(flag is not False for flag in row[2:])):
            raise RuntimeError("Wrong demo database or excessive database privileges")
        cursor.execute("""
            SELECT purpose, schema_version FROM fwms_demo_meta.environment
            WHERE singleton = true
        """)
        if cursor.fetchone() != ("synthetic-only", 1):
            raise RuntimeError("Demo-only schema marker missing")
        cursor.execute("""
            SELECT has_schema_privilege(current_user, 'public', 'CREATE'),
                   has_schema_privilege(current_user, 'fwms_demo_meta', 'CREATE'),
                   has_table_privilege(current_user, 'fwms_demo_meta.environment',
                                       'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
        """)
        permissions = cursor.fetchone()
        if (not permissions or len(permissions) != 3
                or any(flag is not False for flag in permissions)):
            raise RuntimeError("Demo role can alter schema or isolation marker")
        # Prevent alternate schemas from shadowing the verified application's tables.
        cursor.execute("SET SESSION search_path TO public")
        connection.commit()
    except Exception:
        connection.rollback()
        raise RuntimeError("Demo database isolation verification failed") from None
    finally:
        cursor.close()


def accept_token_environment(payload, demo_mode):
    if demo_mode:
        return payload.get("iss") == DEMO_ISSUER and payload.get("aud") == DEMO_ISSUER
    return payload.get("iss") != DEMO_ISSUER
