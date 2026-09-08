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


class SkippedMigrationError(OutOfOrderMigrationError):
    pass


def _base_pulou(known: set[str], version: str) -> bool:
    # Invariante: a base pulou a versão se ela registrou alguma anterior E
    # alguma posterior. Sem a anterior, esta base é nova e só está começando
    # numa árvore que já tem números altos — caso diferente, e não é vão.
    return any(v < version for v in known) and any(v > version for v in known)


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
    # Reason: executescript commits whatever is open before running, so the
    # DDL is fed statement by statement inside an explicit transaction instead.
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
                if version >= highest_known:
                    continue
                # Decisão: duas situações chegam aqui e pedem conselhos
                # opostos. Uma migração que nasceu agora com número baixo se
                # renumera. Uma que já existia e que ESTA base pulou não se
                # renumera — renumerá-la faria toda outra base reaplicá-la. A
                # segunda se reconhece pelo vão: a base tem versões acima dela
                # e não tem ela.
                if _base_pulou(known, version):
                    raise SkippedMigrationError(
                        f"esta base pulou a migração {version}: ela tem {highest_known} "
                        f"aplicada e {version} não. Confira o que {version} faz e, se ela "
                        f"couber no esquema atual, reconcilie com "
                        f"`python -m app.migrate --reconciliar {version}`"
                    )
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


def reconcile_skipped(conn: sqlite3.Connection, folder: Path, version: str) -> str:
    # Decisão: reconciliar TENTA aplicar, e só registra sem aplicar quando o
    # esquema já tem o que a migração criaria. Registrar às cegas é assinar que
    # o esquema está certo sem olhar — e foi assim que esta base ficou com um
    # vão em primeiro lugar.
    conn.execute(CONTROL_TABLE)
    known = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    if version in known:
        return f"a migração {version} já está registrada nesta base; nada a fazer"

    highest_known = max(known, default=None)
    if highest_known is not None and version < highest_known and not _base_pulou(known, version):
        return (
            f"a migração {version} não é um vão desta base: ela não tem versão registrada "
            f"abaixo de {version}, então {version} é migração nova com número baixo. "
            f"Renumere o arquivo para uma versão maior que {highest_known} em vez de "
            "reconciliar — reconciliar aqui recria o vão que este guarda existe para fechar"
        )

    achados = [p for p in folder.glob("*.sql") if _version_of(p) == version]
    if not achados:
        return f"não existe migração {version} em {folder}"
    caminho = achados[0]

    previous_isolation = conn.isolation_level
    conn.isolation_level = None
    try:
        conn.execute("BEGIN")
        try:
            for statement in _statements(caminho.read_text(encoding="utf-8")):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, datetime.now(UTC).isoformat()),
            )
        except Exception as falha:
            conn.execute("ROLLBACK")
            return (
                f"a migração {version} não se aplica ao esquema atual desta base: {falha}. "
                "Nada foi gravado — o vão continua, e reconciliar exige olhar o arquivo"
            )
        conn.execute("COMMIT")
        return f"migração {version} aplicada e registrada; o vão desta base fechou"
    finally:
        conn.isolation_level = previous_isolation
