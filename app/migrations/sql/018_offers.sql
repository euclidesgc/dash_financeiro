CREATE TABLE offers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    monthly_rate_bp INTEGER,
    term_months INTEGER NOT NULL,
    released_cents INTEGER NOT NULL,
    fee_cents INTEGER NOT NULL DEFAULT 0,
    captured_at TEXT NOT NULL
);
