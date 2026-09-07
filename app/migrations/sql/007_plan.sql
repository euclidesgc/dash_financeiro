CREATE TABLE plan_snapshots (
    id INTEGER PRIMARY KEY,
    taken_at TEXT NOT NULL,
    reference_date TEXT NOT NULL,
    scenario TEXT NOT NULL,
    monthly_result_cents INTEGER NOT NULL,
    reserve_target_cents INTEGER NOT NULL,
    -- Null when the objective is not reached under this scenario. Null is the
    -- honest answer: a very large number would read as a date far away, and this
    -- is not far away — it is never, until something changes.
    months_to_objective INTEGER,
    UNIQUE (reference_date, scenario)
);
