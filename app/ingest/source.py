import glob
import json
import os
from typing import Any

DISCARDED_FILE = "descartadas.json"


def load_transactions(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        return _records(json.load(handle))


def load_discarded(transactions_path: str) -> list[str]:
    # Reason: the consolidation drops the pending purchases Pluggy no longer
    # returns and names them in a file beside the consolidated one. An
    # upsert never removes a row, so without this list the base would keep
    # counting them after the source stopped carrying them. A consolidated
    # file made before the list existed has nothing to discard.
    path = os.path.join(os.path.dirname(transactions_path), DISCARDED_FILE)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [str(identifier) for identifier in json.load(handle)]


def load_accounts(pattern: str) -> list[dict[str, Any]]:
    # Reason: every extraction writes a dated accounts_*.json per connection
    # and the old ones stay on disk, so the same account arrives once per
    # snapshot. The loader compares accepted with present by id, and a
    # repeated id made it refuse the whole run. The most recently updated
    # record wins — file names carry the connection id, not the date, so
    # their sort order says nothing about which snapshot is newer.
    by_id: dict[Any, dict[str, Any]] = {}
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as handle:
            for account in _records(json.load(handle)):
                known = by_id.get(account.get("id"))
                if known is None or _updated(known) <= _updated(account):
                    by_id[account.get("id")] = account
    return list(by_id.values())


def _updated(account: dict[str, Any]) -> str:
    return str(account.get("updatedAt") or "")


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return list(payload.get("results", []))
    return list(payload)
