import os
import shutil
import tempfile
from pathlib import Path

from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations

target = os.environ["DASH_DB_PATH"]
Path(target).unlink(missing_ok=True)

with tempfile.TemporaryDirectory() as folder:
    older = Path(folder)
    for path in sorted(SQL_FOLDER.glob("*.sql")):
        if path.stem.split("_", 1)[0] < "010":
            shutil.copy(path, older / path.name)
    conn = connect(target)
    print("até 009:", apply_migrations(conn, older))
    conn.execute(
        "INSERT INTO plan_facts (name, label, value_cents, unit, source, captured_at) "
        "VALUES ('taxa-observada', 'Taxa observada', 100, 'centavos', 'humano', '2026-08-01')"
    )
    conn.execute(
        "INSERT INTO plan_parameters (name, value_cents, updated_at) "
        "VALUES ('quitacao', 3500000, '2026-09-01T10:00:00')"
    )
    conn.commit()
    print("migração:", apply_migrations(conn, SQL_FOLDER))
    print("linha preexistente:", tuple(conn.execute(
        "SELECT name, value, kind FROM plan_facts WHERE name = 'taxa-observada'"
    ).fetchone()))
    conn.close()
