from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import connect
from app.queries.pluggy_connections import ConnectionRow, get_connection, list_connections
from app.sync.connections import (
    ConnectionNotFoundError,
    DuplicateConnectionError,
    InvalidItemIdError,
    add_connection,
    remove_connection,
)

router = APIRouter(prefix="/api/pluggy-connections")

INVALID_ITEM_ID = "Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12)."
DUPLICATE = "Essa conexão já está cadastrada."
NOT_FOUND = "Conexão não encontrada."


class ConnectionOut(BaseModel):
    item_id: str
    created_at: str


class ConnectionsResponse(BaseModel):
    connections: list[ConnectionOut]


class ConnectionInput(BaseModel):
    item_id: str


def _out(row: ConnectionRow) -> ConnectionOut:
    return ConnectionOut(item_id=row.item_id, created_at=row.created_at)


@contextmanager
def _translated() -> Iterator[None]:
    try:
        yield
    except InvalidItemIdError as error:
        raise HTTPException(status_code=422, detail=INVALID_ITEM_ID) from error
    except DuplicateConnectionError as error:
        raise HTTPException(status_code=409, detail=DUPLICATE) from error
    except ConnectionNotFoundError as error:
        raise HTTPException(status_code=404, detail=NOT_FOUND) from error


@router.get("")
def connections() -> ConnectionsResponse:
    conn = connect()
    try:
        rows = list_connections(conn)
    finally:
        conn.close()
    return ConnectionsResponse(connections=[_out(row) for row in rows])


@router.post("", status_code=201)
def add(body: ConnectionInput) -> ConnectionOut:
    conn = connect()
    try:
        with _translated():
            item_id = add_connection(conn, body.item_id)
        row = get_connection(conn, item_id)
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return _out(row)


@router.delete("/{item_id}", status_code=204)
def remove(item_id: str) -> None:
    conn = connect()
    try:
        with _translated():
            remove_connection(conn, item_id)
    finally:
        conn.close()
