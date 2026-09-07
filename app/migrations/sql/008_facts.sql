CREATE TABLE plan_facts (
    name TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    value_cents INTEGER NOT NULL,
    unit TEXT NOT NULL,
    source TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    -- A fact about money goes stale: a payoff balance quoted in September is not
    -- the payoff balance in December. Null means it does not expire.
    valid_until TEXT
);

CREATE TABLE scenarios (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    monthly_cents INTEGER NOT NULL,
    once_cents INTEGER NOT NULL DEFAULT 0,
    months INTEGER,
    starts_on TEXT
);
