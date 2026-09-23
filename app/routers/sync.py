import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import reference_date
from app.db import connect
from app.sync import MissingCredentialError, last_runs, readable
from app.sync.exclusive import SyncBusyError, exclusive_synchronise, is_synchronising

router = APIRouter(prefix="/api/sync")


class SyncRun(BaseModel):
    finished_at: str | None
    status: Literal["ok", "failed"]
    reason: str | None


class SyncStatus(BaseModel):
    running: bool
    last_run: SyncRun | None


def _status(conn: sqlite3.Connection) -> SyncStatus:
    latest = last_runs(conn)["latest"]
    if latest is None:
        return SyncStatus(running=is_synchronising(), last_run=None)
    return SyncStatus(
        running=is_synchronising(),
        last_run=SyncRun(
            finished_at=latest["finished_at"],
            status=latest["status"],
            reason=readable(latest["message"]) if latest["status"] == "failed" else None,
        ),
    )


@router.get("/status")
def sync_status() -> SyncStatus:
    conn = connect()
    try:
        return _status(conn)
    finally:
        conn.close()


@router.post("/run")
def sync_run() -> SyncStatus:
    conn = connect()
    try:
        try:
            exclusive_synchronise(conn, today=reference_date())
        except SyncBusyError as busy:
            raise HTTPException(status_code=409, detail=str(busy)) from busy
        except MissingCredentialError as refusal:
            raise HTTPException(status_code=503, detail=str(refusal)) from refusal
        return _status(conn)
    finally:
        conn.close()
