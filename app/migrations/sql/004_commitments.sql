CREATE TABLE commitments (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    series_key TEXT NOT NULL,
    description TEXT NOT NULL,
    account TEXT,
    amount_cents INTEGER NOT NULL,
    months_observed INTEGER,
    months_consecutive INTEGER,
    last_seen_date TEXT NOT NULL,
    due_day INTEGER,
    last_installment INTEGER,
    installment_total INTEGER NOT NULL DEFAULT 0,
    installments_left INTEGER,
    ends_month TEXT,
    dismissed INTEGER NOT NULL DEFAULT 0,
    UNIQUE (kind, series_key, installment_total, amount_cents)
);

CREATE TABLE commitment_dismissals (
    series_key TEXT PRIMARY KEY,
    dismissed_at TEXT NOT NULL
);

CREATE INDEX idx_commitments_series_key ON commitments (series_key);
