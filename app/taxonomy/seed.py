import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from app.db import connect

SEED_PATH = Path(__file__).resolve().parent / "seed.json"


def load_seed(path: Path | None = None) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((path or SEED_PATH).read_text(encoding="utf-8")))


def message(key: str, value: object, seed: dict[str, Any] | None = None) -> str:
    template = cast(str, (seed or load_seed())["messages"][key])
    return template.format(value=value)


def category_labels() -> dict[str, str]:
    return {entry["name"]: entry["label"] for entry in load_seed()["categories"]}


def seed_taxonomy(conn: sqlite3.Connection, seed: dict[str, Any] | None = None) -> None:
    # Reason: this reconciles instead of only inserting — the CLI is the one
    # path that carries a renamed vocabulary to a database the owner already
    # seeded, and ON CONFLICT DO NOTHING would leave a retired group name
    # standing forever (app/db.py:27 then blocks its deletion once a rule or
    # transaction still points at it).
    data = seed or load_seed()
    conn.executemany(
        "INSERT INTO category_groups (name, position, is_fallback) VALUES (?, ?, ?) "
        "ON CONFLICT (name) DO UPDATE SET "
        "position = excluded.position, is_fallback = excluded.is_fallback",
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
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT (match_kind, match_value) "
        "DO UPDATE SET group_id = excluded.group_id",
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
    # Reason: written before the retired groups are deleted below — a
    # category the owner's machine already carries under an old vocabulary
    # can still be pointing at one of them, and app/db.py:27 blocks the
    # delete while it does.
    conn.executemany(
        "INSERT INTO categories (name, group_id) VALUES (?, ?) "
        "ON CONFLICT (name) DO UPDATE SET group_id = excluded.group_id",
        [(entry["name"], groups[entry["group"]]) for entry in data["categories"]],
    )
    declared_names = [entry["name"] for entry in data["groups"]]
    declared_ids = [groups[name] for name in declared_names]
    fallback_id = next(groups[entry["name"]] for entry in data["groups"] if entry["is_fallback"])
    placeholders = ", ".join("?" for _ in declared_ids)
    conn.execute(
        f"UPDATE category_rules SET group_id = ? WHERE group_id NOT IN ({placeholders})",
        (fallback_id, *declared_ids),
    )
    conn.execute(
        f"UPDATE categories SET group_id = ? WHERE group_id NOT IN ({placeholders})",
        (fallback_id, *declared_ids),
    )
    # Decision: not scoped to "group_id NOT IN declared_ids". A rule reassigned between
    # two groups that both survive the reconciliation leaves its transactions'
    # group_id inside the declared set, just pointing at the wrong member of
    # it, and that earlier scope let those rows pass untouched.
    conn.execute(
        "UPDATE transactions SET group_id = "
        "(SELECT r.group_id FROM category_rules AS r WHERE r.id = transactions.rule_id) "
        "WHERE rule_id IS NOT NULL AND group_id != "
        "(SELECT r.group_id FROM category_rules AS r WHERE r.id = transactions.rule_id)"
    )
    conn.execute(
        f"UPDATE transactions SET group_id = ? "
        f"WHERE group_id NOT IN ({placeholders}) AND rule_id IS NULL",
        (fallback_id, *declared_ids),
    )
    conn.execute(
        f"DELETE FROM category_groups WHERE name NOT IN ({', '.join('?' for _ in declared_names)})",
        declared_names,
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
            "(SELECT count(*) FROM category_rules), (SELECT count(*) FROM categories)"
        ).fetchone()
    finally:
        conn.close()
    print(
        f"taxonomy seeded: groups={counts[0]} natures={counts[1]} "
        f"essentialities={counts[2]} crossings={counts[3]} rules={counts[4]} "
        f"categories={counts[5]}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
