CREATE TABLE financings (
    kind TEXT NOT NULL PRIMARY KEY,
    monthly_rate_bp INTEGER NOT NULL,
    term_months INTEGER NOT NULL,
    -- Null for the vehicle: its balance is the present value of what is left,
    -- recomputed on every rebuild, never stored (norm 23). Negative when
    -- present, like every other value in this base (invariant 22).
    balance_cents INTEGER,
    -- Null for the mortgage, which has no instalment of its own.
    payment_cents INTEGER,
    first_due_date TEXT
);
