"""Fail-closed demo launcher. Never call institutional startup/migration scripts."""
import logging
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def validate_startup(env):
    if env.get('FWMS_DEMO_MODE', '').lower() != 'true':
        raise RuntimeError('Dedicated launcher requires FWMS_DEMO_MODE')
    from app.demo.config import demo_settings_from_env
    configuration = demo_settings_from_env(env)
    try:
        port = int(env.get('PORT', '8000'))
    except (ValueError, TypeError):
        raise RuntimeError('Invalid PORT') from None
    if not 1 <= port <= 65535:
        raise RuntimeError('Invalid PORT')
    return configuration, port


def redact(text, secrets):
    for secret in sorted((value for value in secrets if value), key=len, reverse=True):
        text = text.replace(secret, '[REDACTED]')
        text = text.replace(json.dumps(secret)[1:-1], '[REDACTED]')
    text = re.sub(r'postgres(?:ql)?(?:\+[\w]+)?://[^\s"\'<>]+', '[REDACTED DATABASE URL]', text, flags=re.I)
    text = re.sub(r'Bearer\s+[^\s"\'<>]+', 'Bearer [REDACTED]', text, flags=re.I)
    return re.sub(r'eyJ[\w-]+\.[\w-]+\.[\w-]+', '[REDACTED TOKEN]', text)


class RedactingFormatter(logging.Formatter):
    def __init__(self, delegate, secrets):
        super().__init__()
        self.delegate, self.secrets = delegate, secrets

    def format(self, record):
        # Redact the fully formatted output, including traceback and JSON extras.
        try:
            return redact(self.delegate.format(record), self.secrets)
        except Exception:
            return 'Demo log event suppressed (formatting error)'


def main():
    try:
        configuration, port = validate_startup(os.environ)
        secrets = (configuration['DATABASE_URL'], configuration['SECRET_KEY'])
        # Ordinary configuration cannot be consumed by accidentally imported code.
        for name in ('DATABASE_URL', 'SECRET_KEY', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
                     'GOOGLE_REDIRECT_URI', 'REDIS_URL', 'DEV_AUTH_BYPASS'):
            os.environ.pop(name, None)
        import uvicorn
        from app import main as application
        original_logging = application.configure_logging

        def configure_demo_logging():
            original_logging()
            for handler in logging.getLogger().handlers:
                handler.setFormatter(RedactingFormatter(handler.formatter or logging.Formatter(), secrets))

        application.configure_logging = configure_demo_logging
        safe_formatter = lambda: RedactingFormatter(logging.Formatter('%(levelname)s: %(message)s'), secrets)
        uvicorn.run(application.app, host='0.0.0.0', port=port, access_log=False,
                    log_config={'version': 1, 'disable_existing_loggers': False,
                                'formatters': {'safe': {'()': safe_formatter}},
                                'handlers': {'safe': {'class': 'logging.StreamHandler', 'formatter': 'safe'}},
                                'loggers': {'uvicorn': {'handlers': ['safe'], 'level': 'INFO', 'propagate': False},
                                            'uvicorn.error': {'level': 'INFO'},
                                            'uvicorn.access': {'handlers': [], 'propagate': False}}})
        return 0
    except Exception as error:
        print('Dedicated demo startup refused (' + type(error).__name__ + '). Check demo configuration and isolation prerequisites.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
