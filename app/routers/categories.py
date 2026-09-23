import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import connect
from app.queries.categories import CategoryRow, get_category, list_categories
from app.taxonomy.catalogue import (
    CategoryInUseError,
    CategoryNotFoundError,
    DuplicateLabelError,
    InvalidLabelError,
    InvalidLimitError,
    SystemCategoryError,
    create_category,
    delete_category,
    rename_category,
    set_monthly_limit,
)

router = APIRouter(prefix="/api/categories")

INVALID_LABEL = "Informe o nome da categoria."
DUPLICATE_LABEL = "Já existe uma categoria com esse nome."
NOT_FOUND = "Categoria não encontrada."
SYSTEM_CATEGORY = "Categoria do sistema não pode ser apagada."
INVALID_LIMIT = "O limite precisa ser maior que zero."


def _in_use_detail(count: int) -> str:
    if count == 1:
        return "Esta categoria está em uso por 1 gasto."
    return f"Esta categoria está em uso por {count} gastos."


class CategoryOut(BaseModel):
    key: str
    label: str
    is_system: bool
    usage_count: int
    monthly_limit_cents: int | None


class CategoriesResponse(BaseModel):
    categories: list[CategoryOut]


class CategoryInput(BaseModel):
    label: str


class CategoryLimitInput(BaseModel):
    monthly_limit_cents: int | None


def _out(row: CategoryRow) -> CategoryOut:
    return CategoryOut(
        key=row.key,
        label=row.label,
        is_system=row.is_system,
        usage_count=row.usage_count,
        monthly_limit_cents=row.monthly_limit_cents,
    )


@contextmanager
def _translated() -> Iterator[None]:
    try:
        yield
    except InvalidLabelError as error:
        raise HTTPException(status_code=422, detail=INVALID_LABEL) from error
    except DuplicateLabelError as error:
        raise HTTPException(status_code=422, detail=DUPLICATE_LABEL) from error
    except InvalidLimitError as error:
        raise HTTPException(status_code=422, detail=INVALID_LIMIT) from error
    except CategoryNotFoundError as error:
        raise HTTPException(status_code=404, detail=NOT_FOUND) from error
    except SystemCategoryError as error:
        raise HTTPException(status_code=403, detail=SYSTEM_CATEGORY) from error
    except CategoryInUseError as error:
        raise HTTPException(status_code=409, detail=_in_use_detail(error.usage_count)) from error


def _fetch(conn: sqlite3.Connection, key: str) -> CategoryOut:
    row = get_category(conn, key)
    if row is None:
        raise HTTPException(404, NOT_FOUND)
    return _out(row)


@router.get("")
def categories() -> CategoriesResponse:
    conn = connect()
    try:
        rows = list_categories(conn)
    finally:
        conn.close()
    return CategoriesResponse(categories=[_out(row) for row in rows])


@router.post("", status_code=201)
def create(body: CategoryInput) -> CategoryOut:
    conn = connect()
    try:
        with _translated():
            key = create_category(conn, body.label)
        return _fetch(conn, key)
    finally:
        conn.close()


@router.patch("/{key}")
def rename(key: str, body: CategoryInput) -> CategoryOut:
    conn = connect()
    try:
        with _translated():
            rename_category(conn, key, body.label)
        return _fetch(conn, key)
    finally:
        conn.close()


@router.put("/{key}/limit")
def set_limit(key: str, body: CategoryLimitInput) -> CategoryOut:
    conn = connect()
    try:
        with _translated():
            set_monthly_limit(conn, key, body.monthly_limit_cents)
        return _fetch(conn, key)
    finally:
        conn.close()


@router.delete("/{key}", status_code=204)
def delete(key: str) -> None:  # gate7-ok: nome da rota; o DELETE SQL mora em catalogue.py
    conn = connect()
    try:
        with _translated():
            delete_category(conn, key)
    finally:
        conn.close()
