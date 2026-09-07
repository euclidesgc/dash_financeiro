import json
import sqlite3
from pathlib import Path
from typing import Any

from app.db import connect

SEED_PATH = Path(__file__).resolve().parent / "seed.json"


def load_seed(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or SEED_PATH).read_text(encoding="utf-8"))


def message(key: str, value: object, seed: dict[str, Any] | None = None) -> str:
    return (seed or load_seed())["messages"][key].format(value=value)


def seed_taxonomy(conn: sqlite3.Connection, seed: dict[str, Any] | None = None) -> None:
    data = seed or load_seed()
    conn.executemany(
        "INSERT INTO category_groups (name, position, is_fallback) VALUES (?, ?, ?) "
        "ON CONFLICT (name) DO NOTHING",
        [
            (entry["name"], entry["position"], int(bool(entry["is_fallback"])))
            for entry in data["groups"]
        ],
    )
    _seed_terms(conn, "natures", data["natures"], data["fallback_nature"])
    _seed_terms(conn, "essentialities", data["essentialities"], data["fallback_essentiality"])
    conn.executemany(
        "INSERT INTO crossings (slug, label, nature, essentiality, position) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT (slug) DO NOTHING",
        [
            (
                entry["slug"],
                entry["label"],
                entry["nature"],
                entry["essentiality"],
                entry["position"],
            )
            for entry in data["crossings"]
        ],
    )
    groups = {
        row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM category_groups")
    }
    conn.executemany(
        "INSERT INTO category_rules (match_kind, match_value, group_id, nature, essentiality) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT (match_kind, match_value) DO NOTHING",
        [
            (
                entry["match_kind"],
                entry["match_value"],
                groups[entry["group"]],
                entry["nature"],
                entry["essentiality"],
            )
            for entry in data["rules"]
        ],
    )
    conn.commit()


def _seed_terms(conn: sqlite3.Connection, table: str, values: list[str], fallback: str) -> None:
    conn.executemany(
        f"INSERT INTO {table} (value, position, is_fallback) VALUES (?, ?, ?) "
        "ON CONFLICT (value) DO NOTHING",
        [(value, index + 1, int(value == fallback)) for index, value in enumerate(values)],
    )


def main() -> int:
    conn = connect()
    try:
        seed_taxonomy(conn)
        counts = conn.execute(
            "SELECT (SELECT count(*) FROM category_groups), (SELECT count(*) FROM natures), "
            "(SELECT count(*) FROM essentialities), (SELECT count(*) FROM crossings), "
            "(SELECT count(*) FROM category_rules)"
        ).fetchone()
    finally:
        conn.close()
    print(
        f"taxonomy seeded: groups={counts[0]} natures={counts[1]} "
        f"essentialities={counts[2]} crossings={counts[3]} rules={counts[4]}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
