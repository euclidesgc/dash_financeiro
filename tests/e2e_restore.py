import sqlite3
import sys


def restore(snapshot: str, target: str) -> None:
    # Reason: the e2e server keeps serving while this runs; the backup API
    # takes the database locks, which a plain file copy would ignore.
    source = sqlite3.connect(snapshot)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m tests.e2e_restore <snapshot> <target>", file=sys.stderr)
        return 1
    restore(argv[0], argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
