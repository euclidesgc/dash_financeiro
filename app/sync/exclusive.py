import sqlite3
import threading
from datetime import date

from app.sync import SyncOutcome, synchronise

BUSY_MESSAGE = "Já existe uma atualização em andamento."

# Reason: a process lock, not a database lock — this is the only process that
# serves the screen, and the daily command runs at another hour (D3).
_LOCK = threading.Lock()


class SyncBusyError(RuntimeError):
    pass


def is_synchronising() -> bool:
    return _LOCK.locked()


def exclusive_synchronise(conn: sqlite3.Connection, *, today: date | None = None) -> SyncOutcome:
    if not _LOCK.acquire(blocking=False):
        raise SyncBusyError(BUSY_MESSAGE)
    try:
        return synchronise(conn, today=today)
    finally:
        _LOCK.release()
