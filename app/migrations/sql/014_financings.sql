CREATE TABLE financings (
    kind TEXT NOT NULL PRIMARY KEY,
    monthly_rate_bp INTEGER NOT NULL,
    term_months INTEGER NOT NULL,
    -- Null for the vehicle: its balance is the present value of what is left,
    -- recomputed on every rebuild, never stored (norm 23). Negative when
    -- present, like every other value in this base (invariant 22).
    balance_cents INTEGER,
    -- Null for the mortgage, which has no instalment of its own; required for
    -- the vehicle, whose balance formula divides by neither and instead reads
    -- both to know what is left to discount. The CHECK below guards structural
    -- completeness of the row, not the grammar of a typed field (RF-08 still
    -- refuses in pt-BR before any write reaches this table).
    payment_cents INTEGER,
    first_due_date TEXT,
    CHECK (kind != 'vehicle' OR (payment_cents IS NOT NULL AND first_due_date IS NOT NULL))
);
