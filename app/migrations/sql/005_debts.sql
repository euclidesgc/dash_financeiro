CREATE TABLE debts (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    -- Negative, like every other value in this base: money leaving, in any kind
    -- of account (invariant 22).
    balance_cents INTEGER NOT NULL,
    -- Hundredths of a percentage point per month, integer. A rate in floating
    -- point is the multiplier of every other figure on the screen, and 0.0352
    -- is not 0.0352.
    monthly_rate_bp INTEGER,
    term_months INTEGER,
    payment_cents INTEGER,
    source TEXT NOT NULL,
    account_id TEXT,
    UNIQUE (kind, name)
);

CREATE TABLE plan_parameters (
    name TEXT PRIMARY KEY,
    value_cents INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_debts_rate ON debts (monthly_rate_bp DESC);
