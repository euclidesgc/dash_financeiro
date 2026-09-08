import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

CONTROL_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
)
"""


class OutOfOrderMigrationError(RuntimeError):
    pass


_VERSION = re.compile(r"[0-9]{3}")


def _version_of(path: Path) -> str:
    return path.stem.split("_", 1)[0]


def _statements(script: str) -> list[str]:
    statements: list[str] = []
    buffer = ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if buffer.strip() and sqlite3.complete_statement(buffer):
            statements.append(buffer)
            buffer = ""
    remainder = buffer.strip()
    if remainder:
        statements.append(remainder)
    return statements


def apply_migrations(conn: sqlite3.Connection, folder: Path) -> list[str]:
    # executescript commits whatever is open before running, so the DDL is fed
    # statement by statement inside an explicit transaction instead.
    previous_isolation = conn.isolation_level
    conn.isolation_level = None
    try:
        conn.execute(CONTROL_TABLE)
        known = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        highest_known = max(known, default=None)
        pending = []
        for path in sorted(folder.glob("*.sql")):
            version = _version_of(path)
            # Decisão: a ordem e o guarda comparam a versão como texto, e texto
            # só ordena como número enquanto todos tiverem a mesma largura —
            # "9" vem depois de "015". Recusar a largura errada na porta é mais
            # barato que descobrir a inversão numa base já migrada.
            if not _VERSION.fullmatch(version):
                raise OutOfOrderMigrationError(
                    f"migração “{path.name}” não começa por três algarismos; "
                    "renomeie para a forma 019_descricao.sql"
                )
            if version not in known:
                pending.append((path, version))
        if highest_known is not None:
            for _, version in pending:
                if version < highest_known:
                    raise OutOfOrderMigrationError(
                        f"migração {version} ordena abaixo da mais recente já "
                        f"aplicada ({highest_known}); renumere o arquivo para uma "
                        f"versão maior que {highest_known}"
                    )
        applied: list[str] = []
        for path, version in pending:
            conn.execute("BEGIN")
            try:
                for statement in _statements(path.read_text(encoding="utf-8")):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, datetime.now(UTC).isoformat()),
                )
            except Exception:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
            applied.append(path.name)
        return applied
    finally:
        conn.isolation_level = previous_isolation
