"""Bounded startup retry for the isolated synthetic-demo database."""

import logging
import time

import psycopg2
from sqlalchemy.exc import OperationalError


logger = logging.getLogger(__name__)

# These are transport failures observed while SQLAlchemy is establishing its
# first PostgreSQL connection.  This deliberately excludes authentication,
# role, database, marker and privilege failures, which must fail closed.
_TRANSIENT_CONNECTION_MESSAGES = (
    "ssl connection has been closed unexpectedly",
    "server closed the connection unexpectedly",
    "connection reset by peer",
)
_DIALECT_INITIALIZATION_STATEMENTS = {"", "show standard_conforming_strings"}


def is_transient_startup_connection_error(error):
    """Return true only for known psycopg2 transport failures during connect."""
    if not isinstance(error, OperationalError):
        return False
    if not isinstance(error.orig, psycopg2.OperationalError):
        return False
    statement = (error.statement or "").strip().lower()
    if statement not in _DIALECT_INITIALIZATION_STATEMENTS:
        return False
    detail = str(error.orig).lower()
    return any(marker in detail for marker in _TRANSIENT_CONNECTION_MESSAGES)


def verify_demo_startup_database(engine, *, attempts=3, delay_seconds=0.5, sleep=time.sleep):
    """Open a verified demo connection, retrying only transient establishment errors.

    Each successful checkout still invokes the engine's demo isolation listener,
    so a retry never bypasses database, role, marker or privilege validation.
    """
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect():
                return
        except Exception as error:
            if not is_transient_startup_connection_error(error) or attempt == attempts:
                raise
            logger.warning(
                "Transient demo database connection failure during startup; retrying (%s/%s)",
                attempt,
                attempts,
            )
            sleep(delay_seconds * (2 ** (attempt - 1)))
