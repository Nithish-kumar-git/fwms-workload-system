"""Institutional serving only: no SQL, migrations, seeds or provisioning."""
import logging
import os
import sys

from app.core.log_redaction import RedactingFormatter


def main():
    try:
        if os.environ.get('FWMS_DEMO_MODE', 'false').lower() != 'false':
            raise RuntimeError('Use the dedicated demo launcher')
        port = int(os.environ.get('PORT', '8000'))
        if not 1 <= port <= 65535:
            raise ValueError('Invalid PORT')
        from app.core.config import settings
        from app.main import app
        import uvicorn

        secrets = (settings.DATABASE_URL, settings.SECRET_KEY,
                   settings.GOOGLE_CLIENT_SECRET, settings.SMTP_PASSWORD)
        uvicorn.run(app, host='0.0.0.0', port=port, access_log=False,
                    log_config={
                        'version': 1, 'disable_existing_loggers': False,
                        'formatters': {'safe': {'()': lambda: RedactingFormatter(
                            logging.Formatter('%(levelname)s: %(message)s'), secrets)}},
                        'handlers': {'safe': {'class': 'logging.StreamHandler', 'formatter': 'safe'}},
                        'loggers': {'uvicorn': {'handlers': ['safe'], 'level': 'INFO', 'propagate': False},
                                    'uvicorn.error': {'level': 'INFO'},
                                    'uvicorn.access': {'handlers': [], 'propagate': False}},
                    })
        return 0
    except (Exception, SystemExit) as error:
        print('Backend startup refused (' + type(error).__name__ +
              '). Check required configuration privately.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
