import glob
import json
from typing import Any


def load_transactions(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        return _records(json.load(handle))


def load_accounts(pattern: str) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as handle:
            accounts.extend(_records(json.load(handle)))
    return accounts


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return list(payload.get("results", []))
    return list(payload)
