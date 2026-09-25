-- Null only for runs written before this migration: who asked for a past run
-- is recorded nowhere, and inventing it would be worse than not having it.
ALTER TABLE sync_runs ADD COLUMN triggered_by TEXT NULL CHECK (triggered_by IS NULL OR triggered_by IN ('screen', 'command'));
