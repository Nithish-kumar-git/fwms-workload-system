"""Coordinate derived-workload writers before taking any row locks.

One database-local transaction advisory lock deliberately serializes these
infrequent administrative operations. No schema or elevated role is required.
All participating writers take this lock first, including an entire batch.
"""
from contextlib import contextmanager
from sqlalchemy import text
from app.db.session import get_transaction

# Reserved FWMS namespace and workload-operation key (two signed int32 values).
WORKLOAD_LOCK = (1179995475, 1)


@contextmanager
def workload_transaction():
    with get_transaction() as session:
        # get_transaction sets the existing five-second lock timeout first.
        # COMMIT, ROLLBACK or connection loss releases this transaction lock.
        session.execute(text("SELECT pg_advisory_xact_lock(:namespace, :key)"),
                        {"namespace": WORKLOAD_LOCK[0], "key": WORKLOAD_LOCK[1]})
        yield session
