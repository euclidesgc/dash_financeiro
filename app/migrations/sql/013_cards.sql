-- A separate table, not a column on accounts: accounts is upserted from the
-- source on every load (app/ingest/loader.py:136), and a column the owner
-- filled in would be silently overwritten by the next sync.
CREATE TABLE cards (
    account_id TEXT PRIMARY KEY NOT NULL REFERENCES accounts(id),
    limit_cents INTEGER,
    monthly_rate_bp INTEGER,
    closing_day INTEGER,
    due_day INTEGER,
    CHECK (closing_day IS NULL OR closing_day BETWEEN 1 AND 31),
    CHECK (due_day IS NULL OR due_day BETWEEN 1 AND 31)
);

-- MAX(...) because a bare subselect would pick whichever row SQLite happens to
-- read first when two exist, and the figure the owner sees cannot depend on
-- physical row order.
INSERT INTO cards (account_id, monthly_rate_bp)
SELECT a.id,
       (SELECT MAX(d.monthly_rate_bp) FROM debts d
         WHERE d.kind = 'card' AND d.account_id = a.id)
  FROM accounts a WHERE a.type = 'CREDIT';

-- Restricted to account_id IS NOT NULL: a card step with no account (the two
-- fixtures of another item that insert one directly) has nowhere to move to,
-- and nulling its rate here would lose the value with no new home for it.
UPDATE debts SET monthly_rate_bp = NULL
 WHERE kind = 'card' AND account_id IS NOT NULL;
