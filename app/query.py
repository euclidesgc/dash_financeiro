import sys

from app.db import connect

ALLOWED_KEYWORDS = ("select", "pragma")


def is_read_only(statement: str) -> bool:
    head = statement.strip().split(maxsplit=1)
    return bool(head) and head[0].lower() in ALLOWED_KEYWORDS


def run(statement: str) -> int:
    if not is_read_only(statement):
        print("refused: only select and pragma are allowed", file=sys.stderr)
        return 1
    conn = connect()
    try:
        for row in conn.execute(statement):
            print(" ".join("" if value is None else str(value) for value in row))
    finally:
        conn.close()
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print('usage: python -m app.query "<select ...>"', file=sys.stderr)
        return 1
    return run(argv[0])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
