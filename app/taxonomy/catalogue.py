import re
import sqlite3
from typing import cast

from app.db import fold
from app.taxonomy.classify import MissingFallbackError
from app.taxonomy.seed import UNCATEGORISED


class InvalidLabelError(ValueError):
    def __init__(self, label: object) -> None:
        super().__init__(f"rótulo inválido: {label!r}")
        self.label = label


class DuplicateLabelError(ValueError):
    def __init__(self, label: str) -> None:
        super().__init__(f"rótulo duplicado: {label}")
        self.label = label


class CategoryNotFoundError(LookupError):
    def __init__(self, key: str) -> None:
        super().__init__(f"categoria desconhecida: {key}")
        self.key = key


class SystemCategoryError(PermissionError):
    def __init__(self, key: str) -> None:
        super().__init__(f"categoria do sistema: {key}")
        self.key = key


class CategoryInUseError(RuntimeError):
    def __init__(self, key: str, usage_count: int) -> None:
        super().__init__(f"categoria em uso: {key} ({usage_count})")
        self.key = key
        self.usage_count = usage_count


class InvalidLimitError(ValueError):
    def __init__(self, cents: int) -> None:
        super().__init__(f"limite inválido: {cents}")
        self.cents = cents


def slugify(label: str) -> str:
    folded = fold(label) or ""
    slug = re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
    return slug or "categoria"


def _unique_key(conn: sqlite3.Connection, base: str) -> str:
    candidate = base
    suffix = 2
    while conn.execute("SELECT 1 FROM categories WHERE name = ?", (candidate,)).fetchone():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _check_label(conn: sqlite3.Connection, label: str, except_key: str | None = None) -> str:
    clean = label.strip()
    if not clean:
        raise InvalidLabelError(label)
    row = conn.execute(
        "SELECT 1 FROM categories WHERE fold(label) = fold(?) AND name != ?",
        (clean, except_key or ""),
    ).fetchone()
    if row is not None:
        raise DuplicateLabelError(clean)
    return clean


def _require(conn: sqlite3.Connection, key: str) -> sqlite3.Row:
    if key == UNCATEGORISED:
        raise CategoryNotFoundError(key)
    row = conn.execute("SELECT name, is_system FROM categories WHERE name = ?", (key,)).fetchone()
    if row is None:
        raise CategoryNotFoundError(key)
    return cast(sqlite3.Row, row)


def create_category(conn: sqlite3.Connection, label: str) -> str:
    clean = _check_label(conn, label)
    group = conn.execute("SELECT id FROM category_groups WHERE is_fallback = 1").fetchone()
    if group is None:
        raise MissingFallbackError("category_groups")
    key = _unique_key(conn, slugify(clean))
    conn.execute(
        "INSERT INTO categories (name, group_id, label, is_system) VALUES (?, ?, ?, 0)",
        (key, group[0], clean),
    )
    conn.commit()
    return key


def rename_category(conn: sqlite3.Connection, key: str, label: str) -> None:
    _require(conn, key)
    clean = _check_label(conn, label, except_key=key)
    conn.execute("UPDATE categories SET label = ? WHERE name = ?", (clean, key))
    conn.commit()


def set_monthly_limit(conn: sqlite3.Connection, key: str, cents: int | None) -> None:
    _require(conn, key)
    if cents is not None and cents <= 0:
        raise InvalidLimitError(cents)
    conn.execute("UPDATE categories SET monthly_limit_cents = ? WHERE name = ?", (cents, key))
    conn.commit()


def delete_category(conn: sqlite3.Connection, key: str) -> None:
    row = _require(conn, key)
    if row["is_system"]:
        raise SystemCategoryError(key)
    count = conn.execute("SELECT count(*) FROM transactions WHERE category = ?", (key,)).fetchone()[
        0
    ]
    if count > 0:
        raise CategoryInUseError(key, count)
    conn.execute("DELETE FROM categories WHERE name = ?", (key,))
    conn.commit()


# Reason: creating, renaming, deleting or setting the limit of a category
# touches only the categories table — no transaction's classification
# changes, so the taxonomy reclassification step is never invoked here.
