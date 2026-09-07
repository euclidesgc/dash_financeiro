CREATE TABLE advisor_questions (
    name TEXT PRIMARY KEY,
    asked_at TEXT NOT NULL,
    answered_at TEXT,
    -- An ignored question disappears and comes back only when it matters again.
    -- Insisting is how a panel stops being read.
    dismissed_at TEXT
);
