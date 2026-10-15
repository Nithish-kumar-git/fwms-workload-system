"""Demo configuration comes from explicit environment variables, never .env."""

from urllib.parse import parse_qs, urlsplit


def demo_settings_from_env(env):
    mode = env.get("FWMS_DEMO_MODE", "false").lower()
    if mode not in ("true", "false"):
        raise RuntimeError("FWMS_DEMO_MODE must be true or false")
    if mode == "false":
        return None
    required = ("FWMS_DEMO_DATABASE_URL", "FWMS_DEMO_SECRET_KEY", "FWMS_DEMO_FRONTEND_URL")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError("Missing demo configuration: " + ", ".join(missing))
    try:
        db = urlsplit(env["FWMS_DEMO_DATABASE_URL"])
        expected_role = {"/fwms_demo": "fwms_demo_runtime", "/fwms_demo_test": "fwms_demo_test_app"}.get(db.path)
        valid = (db.scheme == "postgresql" and db.hostname and db.username == expected_role
                 and expected_role is not None and not db.fragment
                 and set(parse_qs(db.query)) <= {"sslmode", "connect_timeout"})
        _ = db.port
    except ValueError:
        valid = False
    if not valid:
        raise RuntimeError("Demo database must use its dedicated database and restricted application role")
    secret = env["FWMS_DEMO_SECRET_KEY"]
    if len(secret) < 32:
        raise RuntimeError("FWMS_DEMO_SECRET_KEY must have at least 32 characters")
    try:
        frontend = urlsplit(env["FWMS_DEMO_FRONTEND_URL"])
        valid_frontend = (frontend.hostname and not frontend.username and not frontend.password
                          and not frontend.query and not frontend.fragment and frontend.path in ("", "/")
                          and (frontend.scheme == "https" or (frontend.scheme == "http"
                               and frontend.hostname in ("localhost", "127.0.0.1", "::1"))))
        _ = frontend.port
    except ValueError:
        valid_frontend = False
    if not valid_frontend:
        raise RuntimeError("FWMS_DEMO_FRONTEND_URL must be an HTTPS origin or local HTTP origin")
    return {
        "DEMO_MODE": True, "ENV": "production",
        "DATABASE_URL": env["FWMS_DEMO_DATABASE_URL"], "SECRET_KEY": secret,
        "FRONTEND_URL": env["FWMS_DEMO_FRONTEND_URL"].rstrip("/"),
        "GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": "", "GOOGLE_REDIRECT_URI": "",
        "ALLOWED_EMAIL_DOMAIN": "demo.example.com", "DEV_AUTH_BYPASS": False,
        "SESSION_BACKEND": "memory", "REDIS_URL": None, "EMAIL_BACKEND": "log",
        "SMTP_HOST": None, "SMTP_USER": None, "SMTP_PASSWORD": None,
        "SESSION_COOKIE_NAME": "fwms_demo_session", "SESSION_COOKIE_SECURE": True,
        "POOL_SIZE": 2, "POOL_MAX_OVERFLOW": 2,
        "RATE_LIMIT_BACKEND": "memory", "RATE_LIMIT_ENABLED": True,
    }
