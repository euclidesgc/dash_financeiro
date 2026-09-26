-- A proposal is the only write the advisor prepares; nothing changes until the
-- owner applies it. transaction_id has no foreign key on purpose: ingestion
-- deletes transactions, and the audit trail must neither vanish with them nor
-- block the ingest. The item keeps a snapshot of date, description and amount
-- so the card stays readable.
CREATE TABLE advisor_proposals (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES advisor_conversations (id) ON DELETE CASCADE,
    target_category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'applied', 'discarded', 'undone')),
    created_at TEXT NOT NULL,
    applied_at TEXT NULL,
    discarded_at TEXT NULL,
    undone_at TEXT NULL,
    undo_skipped INTEGER NULL
);

CREATE INDEX advisor_proposals_conversation ON advisor_proposals (conversation_id);

CREATE TABLE advisor_proposal_items (
    id INTEGER PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES advisor_proposals (id) ON DELETE CASCADE,
    transaction_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NULL,
    amount_cents INTEGER NOT NULL,
    previous_category TEXT NULL,
    previous_source TEXT NOT NULL CHECK (previous_source IN ('auto', 'manual')),
    UNIQUE (proposal_id, transaction_id)
);
